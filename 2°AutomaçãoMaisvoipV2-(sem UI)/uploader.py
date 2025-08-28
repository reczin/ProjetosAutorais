import argparse
import json
import os
import sys
import io
import time
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

# Google Drive API
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


# ----------------------------
# Config / Types
# ----------------------------

DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


@dataclass
class DriveFile:
    id: str
    name: str
    mimeType: str
    modifiedTime: str


# ----------------------------
# Google Drive helpers
# ----------------------------

def build_drive(service_account_path: str) -> "Resource":
    creds = service_account.Credentials.from_service_account_file(
        service_account_path, scopes=DRIVE_SCOPES
    )
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def read_folder_id_from_sa(service_account_path: str) -> Optional[str]:
    try:
        data = json.loads(Path(service_account_path).read_text(encoding="utf-8"))
        # Campo custom: drive_folder_id
        return data.get("drive_folder_id")
    except Exception:
        return None


def list_files_in_folder(
    drive,
    folder_id: str,
    allowed_exts: List[str],
    page_size: int = 100,
) -> List[DriveFile]:
    files: List[DriveFile] = []
    page_token = None
    # Query por pasta + filtro de extensões (se houver)
    ext_q = ""
    if allowed_exts:
        # Monta uma OR list para 'name' terminar com as extensões
        or_parts = [f"name contains '.{ext.strip().lower()}'" for ext in allowed_exts if ext.strip()]
        if or_parts:
            ext_q = " and (" + " or ".join(or_parts) + ")"

    base_q = f"'{folder_id}' in parents and trashed = false{ext_q}"

    while True:
        resp = drive.files().list(
            q=base_q,
            fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
            pageToken=page_token,
            pageSize=page_size,
            orderBy="modifiedTime desc",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute()

        for f in resp.get("files", []):
            files.append(
                DriveFile(
                    id=f["id"],
                    name=f["name"],
                    mimeType=f.get("mimeType", ""),
                    modifiedTime=f.get("modifiedTime", ""),
                )
            )

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

    return files


def download_file(
    drive,
    file_id: str,
    local_dir: Path,
    local_name: Optional[str] = None,
    chunk_size: int = 1024 * 1024,
) -> Path:
    local_dir.mkdir(parents=True, exist_ok=True)
    request = drive.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request, chunksize=chunk_size)

    done = False
    while not done:
        status, done = downloader.next_chunk()

    fh.seek(0)
    # Fetch name if not provided
    if not local_name:
        meta = drive.files().get(fileId=file_id, fields="name").execute()
        local_name = meta["name"]

    out_path = local_dir / local_name
    with out_path.open("wb") as f:
        f.write(fh.read())

    return out_path


# ----------------------------
# Playwright helpers
# ----------------------------

def _try_fill(page, locators, value):
    for kind, selector in locators:
        try:
            if kind == "role":
                page.get_by_role(selector["role"], name=selector["name"]).fill(value)
            elif kind == "css":
                page.locator(selector).fill(value)
            elif kind == "placeholder":
                page.get_by_placeholder(selector).fill(value)
            return True
        except Exception:
            continue
    return False


def _try_click(page, locators):
    for kind, selector in locators:
        try:
            if kind == "role":
                page.get_by_role(selector["role"], name=selector["name"]).click()
            elif kind == "css":
                page.locator(selector).click()
            elif kind == "text":
                page.get_by_text(selector).click()
            return True
        except Exception:
            continue
    return False


def login_and_navigate(page, base_url: str, username: str, password: str) -> None:
    page.goto(base_url, wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")

    # Tenta preencher usuário
    filled_user = _try_fill(
        page,
        [
            ("role", {"role": "textbox", "name": re.compile(r"Usu[aá]rio|User", re.I)}),
            ("placeholder", "Usuário"),
            ("css", 'input[name="usuario"], input[name="username"], input[type="text"]'),
        ],
        username,
    )
    if not filled_user:
        raise RuntimeError("Não foi possível localizar o campo de usuário.")

    # Tenta preencher senha
    filled_pass = _try_fill(
        page,
        [
            ("role", {"role": "textbox", "name": re.compile(r"Senha|Password", re.I)}),
            ("placeholder", "Senha"),
            ("css", 'input[name="senha"], input[name="password"], input[type="password"]'),
        ],
        password,
    )
    if not filled_pass:
        raise RuntimeError("Não foi possível localizar o campo de senha.")

    # Tenta clicar no botão de login
    clicked = _try_click(
        page,
        [
            ("role", {"role": "button", "name": re.compile(r"Entrar|Acessar|Login", re.I)}),
            ("css", 'button[type="submit"], input[type="submit"]'),
            ("text", "Entrar"),
        ],
    )
    if not clicked:
        raise RuntimeError("Não foi possível clicar no botão de login.")

    # Aguarda a navegação pós-login
    page.wait_for_load_state("networkidle")

    # Navega até IPBX > Áudio (ajuste se necessário)
    _try_click(page, [("role", {"role": "link", "name": re.compile(r"IPBX", re.I)})])
    page.wait_for_load_state("networkidle")
    _try_click(page, [("role", {"role": "link", "name": re.compile(r"Áudio|Audio", re.I)})])
    page.wait_for_load_state("networkidle")

    # Aguarda o iframe da área de postagem
    page.wait_for_selector('iframe[name="Post"]', timeout=15000)


def upload_one_file(page, local_file_path: Path) -> None:
    frame = page.frame(name="Post")
    if frame is None:
        raise RuntimeError("Iframe 'Post' não encontrado.")

    # Abrir formulário de inserção
    frame.get_by_role("button", name=re.compile(r"Inserir|Novo|Adicionar", re.I)).click()

    # Se existir um Radio de origem local, tente marcá-lo (opcional)
    try:
        frame.locator("#origemArquivoUpload, input#origemArquivoUpload[type='radio']").check(timeout=2000)
    except Exception:
        pass  # nem sempre existe

    # Envia o arquivo direto no input[type=file] (mesmo que esteja hidden)
    frame.set_input_files('input[type="file"]', str(local_file_path))

    # Preenche a descrição com o nome do arquivo (sem extensão)
    try:
        frame.locator("#obj_audio_descricao, input[name='obj_audio_descricao']").fill(local_file_path.stem)
    except Exception:
        pass

    # Salvar
    _ = _try_click(frame, [
        ("role", {"role": "button", "name": re.compile(r"Salvar|Gravar|Enviar", re.I)}),
        ("css", "button#btnSalvar, button[type=submit]"),
    ])

    # Confirmação 'ok' (pode vir como link ou botão; variações de caixa)
    try:
        frame.get_by_role("link", name=re.compile(r"^ok$", re.I)).click(timeout=3000)
    except Exception:
        try:
            frame.get_by_role("button", name=re.compile(r"^ok$", re.I)).click(timeout=2000)
        except Exception:
            pass

    time.sleep(0.5)


# ----------------------------
# Main flow
# ----------------------------

def resolve_folder_id(cli_folder_id: Optional[str], sa_folder_id: Optional[str]) -> str:
    folder_id = cli_folder_id or os.getenv("DRIVE_FOLDER_ID") or sa_folder_id
    if not folder_id:
        raise SystemExit("Defina o ID da pasta do Drive via --drive_folder_id, env DRIVE_FOLDER_ID ou no service-account.json (campo drive_folder_id).")
    return folder_id


def main():
    parser = argparse.ArgumentParser(description="Uploader de áudios (Google Drive -> IPBX)")
    parser.add_argument("--username", required=True, help="Usuário do IPBX (login)")
    parser.add_argument("--password", required=True, help="Senha do IPBX (login)")
    parser.add_argument("--base_url", default=os.getenv("IPBX_URL", "https://seu-dominio:8001/"), help="URL base do IPBX (login)")
    parser.add_argument("--service_account", default="service-account.json", help="Caminho do arquivo service-account.json")
    parser.add_argument("--drive_folder_id", default=None, help="ID da pasta do Drive (opcional)")
    parser.add_argument("--download_dir", default="downloads", help="Diretório local para salvar os áudios baixados")
    parser.add_argument("--allowed_ext", default="mp3,wav,ogg", help="Extensões permitidas quando --all=1 (separadas por vírgula)")
    parser.add_argument("--all", type=int, default=1, choices=[0,1], help="1 = enviar todos os arquivos válidos da pasta; 0 = enviar apenas --filename")
    parser.add_argument("--filename", default=None, help="Nome exato do arquivo a enviar quando --all=0")
    parser.add_argument("--headless", type=int, default=1, choices=[0,1], help="1 = headless, 0 = com janela")

    args = parser.parse_args()

    # Validações básicas
    if args.all == 0 and not args.filename:
        raise SystemExit("Com --all=0 você deve informar --filename.")

    service_account_path = Path(args.service_account)
    if not service_account_path.exists():
        raise SystemExit(f"Arquivo de credenciais não encontrado: {service_account_path}")

    # Build Drive e pasta
    drive = build_drive(str(service_account_path))
    sa_folder_id = read_folder_id_from_sa(str(service_account_path))
    folder_id = resolve_folder_id(args.drive_folder_id, sa_folder_id)

    allowed_exts = [e.strip().lower() for e in args.allowed_ext.split(",") if e.strip()]

    # Lista arquivos
    files = list_files_in_folder(drive, folder_id, allowed_exts=allowed_exts)
    if not files:
        print("Nenhum arquivo encontrado na pasta do Drive com as extensões permitidas.")
        return

    # Seleção de arquivos para enviar
    selected: List[DriveFile] = []
    if args.all == 1:
        selected = files
    else:
        # Só o arquivo solicitado
        found = [f for f in files if f.name == args.filename]
        if not found:
            raise SystemExit(f"Arquivo '{args.filename}' não encontrado na pasta do Drive.")
        selected = found

    # Download para diretório local
    download_dir = Path(args.download_dir)
    download_dir.mkdir(parents=True, exist_ok=True)
    local_paths: List[Path] = []
    for f in selected:
        try:
            lp = download_file(drive, f.id, download_dir, local_name=f.name)
            print(f"Baixado: {lp.name}")
            local_paths.append(lp)
        except Exception as e:
            print(f"Falha ao baixar '{f.name}': {e}")

    if not local_paths:
        print("Nada para enviar (falha no download).")
        return

    # Playwright: login e upload
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=bool(args.headless))
        context = browser.new_context(ignore_https_errors=True)
        page = context.new_page()

        try:
            login_and_navigate(page, base_url=args.base_url, username=args.username, password=args.password)

            for lp in local_paths:
                try:
                    upload_one_file(page, lp)
                    print(f"Enviado: {lp.name}")
                except PlaywrightTimeoutError as te:
                    print(f"Timeout ao enviar '{lp.name}': {te}")
                except Exception as e:
                    print(f"Falha ao enviar '{lp.name}': {e}")

        finally:
            try:
                context.close()
            except Exception:
                pass
            browser.close()

    print("Concluído.")


if __name__ == "__main__":
    main()