import os
import io
import re
import tempfile
from pathlib import Path
from tkinter import Tk, Label, Entry, Button, Listbox, END, SINGLE, StringVar, messagebox
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from googleapiclient.http import MediaIoBaseDownload
from playwright.sync_api import sync_playwright

# ===================== CONFIG SITE =====================
URL = "https://####.maisvoipdiscador.com.br:###/maisvoip/autenticacao.php"
USUARIO = "#####"
SENHA = "##########"

# Selectores
SELECTOR_LOGIN = "#login"
SELECTOR_SENHA = "#senha"
BTN_ENTRAR_NAME = "Entrar"
LINK_IPBX = "IPBX"
MENU_FUNCIONALIDADES_TEXT = "Funcionalidades"
LINK_AUDIO = "Áudio"
IFRAME_NAME = "Post"
BTN_INSERIR_NAME = "Inserir"
RADIO_UPLOAD_ORIGEM = "#origemArquivoUpload"
INPUT_FILE = "input[type='file']"
INPUT_DESCRICAO = "#obj_audio_descricao"
BTN_SALVAR_NAME = "Salvar"

# ===================== CONFIG DRIVE =====================
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

def drive_client():
    if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
        raise RuntimeError("Defina a variável de ambiente GOOGLE_APPLICATION_CREDENTIALS para a Service Account.")
    creds = Credentials.from_service_account_file(os.environ["GOOGLE_APPLICATION_CREDENTIALS"], scopes=SCOPES)
    return build("drive", "v3", credentials=creds)

def extract_id_from_url(url_or_id: str) -> str:
    s = url_or_id.strip()
    if "drive.google.com" in s:
        if "/file/d/" in s:     # arquivo
            return s.split("/file/d/")[1].split("/")[0]
        if "/folders/" in s:    # pasta
            return s.split("/folders/")[1].split("/")[0]
        if "id=" in s:
            return s.split("id=")[1].split("&")[0]
    return s

def is_google_doc_mime(mime: str) -> bool:
    return mime.startswith("application/vnd.google-apps")

def is_audio_mime(mime: str, name: str) -> bool:
    if mime.startswith("audio/"):
        return True
    # fallback por extensão
    ext = Path(name).suffix.lower()
    return ext in {".mp3", ".wav", ".ogg", ".m4a", ".aac", ".flac", ".wma", ".amr", ".gsm", ".g729"}

def export_mime_for(mime: str) -> tuple[str, str]:
    mapping = {
        "application/vnd.google-apps.document": ("application/pdf", ".pdf"),
        "application/vnd.google-apps.spreadsheet": ("text/csv", ".csv"),
        "application/vnd.google-apps.presentation": ("application/pdf", ".pdf"),
        "application/vnd.google-apps.drawing": ("image/png", ".png"),
    }
    return mapping.get(mime, ("application/pdf", ".pdf"))

def download_drive_file(file_id: str, svc, target_dir: str) -> str:
    """Baixa um arquivo do Drive para target_dir e retorna o caminho local."""
    meta = svc.files().get(fileId=file_id, fields="name,mimeType").execute()
    name, mime = meta["name"], meta["mimeType"]
    out_path = os.path.join(target_dir, name)
    fh = io.BytesIO()

    if is_google_doc_mime(mime):
        export_mime, suffix = export_mime_for(mime)
        req = svc.files().export_media(fileId=file_id, mimeType=export_mime)
        out_path = os.path.join(target_dir, name + suffix)
    else:
        req = svc.files().get_media(fileId=file_id)

    downloader = MediaIoBaseDownload(fh, req)
    done = False
    while not done:
        _, done = downloader.next_chunk()

    with open(out_path, "wb") as f:
        f.write(fh.getvalue())
    return out_path

def list_audio_files_in_folder(folder_id: str, svc) -> list[dict]:
    """Retorna lista de dicts {id, name, mimeType} para áudios dentro da pasta."""
    results = []
    page_token = None
    while True:
        resp = svc.files().list(
            q=f"'{folder_id}' in parents and trashed=false and mimeType!='application/vnd.google-apps.folder'",
            fields="nextPageToken, files(id,name,mimeType)",
            pageSize=1000,
            pageToken=page_token
        ).execute()
        for f in resp.get("files", []):
            if is_audio_mime(f.get("mimeType",""), f.get("name","")):
                results.append(f)
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return results

# ===================== PLAYWRIGHT FLOW =====================
def get_post_frame(page):
    page.wait_for_selector(f"iframe[name='{IFRAME_NAME}']")
    frame = page.frame(name=IFRAME_NAME)
    if not frame:
        raise RuntimeError(f"Não foi possível obter o iframe '{IFRAME_NAME}'.")
    return frame

def do_login_and_open_audio(page):
    page.goto(URL, wait_until="domcontentloaded")
    page.fill(SELECTOR_LOGIN, USUARIO)
    page.fill(SELECTOR_SENHA, SENHA)
    page.get_by_role("button", name=BTN_ENTRAR_NAME).click()
    page.get_by_role("link", name=LINK_IPBX).click()
    page.get_by_text(MENU_FUNCIONALIDADES_TEXT).click()
    page.get_by_role("link", name=LINK_AUDIO).click()

def upload_one(page, file_path: str, descricao: str):
    """Executa o envio de UM arquivo já logado/na tela de Áudio."""
    frame = get_post_frame(page)

    # Abre o formulário
    frame.get_by_role("button", name=BTN_INSERIR_NAME).click()
    frame.locator(RADIO_UPLOAD_ORIGEM).check()

    # Arquivo + descrição
    file_input = frame.locator(INPUT_FILE).first
    file_input.set_input_files(str(file_path))
    frame.fill(INPUT_DESCRICAO, descricao)

    # Salvar
    frame.get_by_role("button", name=BTN_SALVAR_NAME).click()
    page.wait_for_timeout(800)  # respiro pra renderizar a tela de confirmação

    # Clicar em "Voltar" (ou "OK") dentro do mesmo iframe
    try:
        frame.get_by_role("link", name=re.compile(r"(voltar|ok)", re.I)).click()
    except Exception:
        try:
            frame.get_by_role("button", name=re.compile(r"(voltar|ok)", re.I)).click()
        except Exception as e:
            print("Aviso: não encontrei 'Voltar/OK' na confirmação:", e)

    # Grace-period para retornar à tela principal do iframe
    page.wait_for_timeout(800)

def upload_many(file_paths_and_names: list[tuple[str,str]], headless: bool = False):
    """Abre 1 navegador e envia todos os arquivos (lista de (caminho, descricao))."""
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        context = browser.new_context()
        context.set_default_timeout(30000)
        page = context.new_page()

        do_login_and_open_audio(page)

        for local_path, descricao in file_paths_and_names:
            try:
                upload_one(page, local_path, descricao)
            except Exception as e:
                print(f"[ERRO] Falha ao enviar {local_path}: {e}")

        context.close()
        browser.close()

# ===================== TKINTER UI =====================
class DrivePickerApp:
    def __init__(self, root):
        self.root = root
        root.title("Selecionar arquivo do Google Drive")
        self.svc = drive_client()
        self.search_results = []  # (id, name, mime)

        Label(root, text="Cole um link/ID do Drive (arquivo ou PASTA):").grid(row=0, column=0, sticky="w", padx=8, pady=(8,2))
        self.link_var = StringVar()
        Entry(root, textvariable=self.link_var, width=60).grid(row=1, column=0, padx=8, sticky="we")
        Button(root, text="Baixar & Enviar (1)", command=self.on_paste_and_send_one).grid(row=1, column=1, padx=8)
        Button(root, text="Enviar TODOS da pasta", command=self.on_paste_and_send_all).grid(row=1, column=2, padx=8)

        Label(root, text="Ou pesquise pelo nome (arquivos):").grid(row=2, column=0, sticky="w", padx=8, pady=(8,2))
        self.query_var = StringVar()
        Entry(root, textvariable=self.query_var, width=40).grid(row=3, column=0, padx=8, sticky="w")
        Button(root, text="Buscar", command=self.on_search).grid(row=3, column=1, padx=8, sticky="w")

        self.listbox = Listbox(root, selectmode=SINGLE, width=80, height=10)
        self.listbox.grid(row=4, column=0, columnspan=3, padx=8, pady=8, sticky="we")
        Button(root, text="Selecionar & Enviar (1)", command=self.on_select_and_send_one).grid(row=5, column=0, padx=8, pady=(0,8), sticky="w")
        Button(root, text="Selecionar & Enviar TODOS (lista)", command=self.on_select_and_send_all_from_list).grid(row=5, column=1, padx=8, pady=(0,8), sticky="w")

    # -------- ações baseadas em link/ID ----------
    def on_paste_and_send_one(self):
        val = self.link_var.get().strip()
        if not val:
            messagebox.showwarning("Atenção", "Cole um link ou ID do Drive.")
            return
        file_or_folder_id = extract_id_from_url(val)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                local_path = download_drive_file(file_or_folder_id, self.svc, tmpdir)
                nome_desc = Path(local_path).stem  # descrição = nome do arquivo sem extensão
                upload_many([(local_path, nome_desc)], headless=False)
            messagebox.showinfo("Sucesso", "Upload concluído.")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha no envio único: {e}")

    def on_paste_and_send_all(self):
        val = self.link_var.get().strip()
        if not val:
            messagebox.showwarning("Atenção", "Cole o link/ID da PASTA do Drive.")
            return
        folder_id = extract_id_from_url(val)
        try:
            audios = list_audio_files_in_folder(folder_id, self.svc)
            if not audios:
                messagebox.showinfo("Atenção", "Nenhum arquivo de áudio encontrado na pasta.")
                return

            with tempfile.TemporaryDirectory() as tmpdir:
                pairs = []
                for f in audios:
                    local_path = download_drive_file(f["id"], self.svc, tmpdir)
                    descricao = Path(local_path).stem
                    pairs.append((local_path, descricao))

                upload_many(pairs, headless=False)

            messagebox.showinfo("Sucesso", f"Uploads concluídos: {len(audios)} arquivo(s).")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao enviar todos da pasta: {e}")

    # -------- busca e lista ----------
    def on_search(self):
        q = self.query_var.get().strip()
        if not q:
            messagebox.showwarning("Atenção", "Digite um termo de busca.")
            return
        resp = self.svc.files().list(
            q=f"name contains '{q.replace('\'', '\\\'')}' and trashed=false",
            fields="files(id,name,mimeType)",
            pageSize=100
        ).execute()
        files = resp.get("files", [])
        self.search_results = [(f["id"], f["name"], f["mimeType"]) for f in files if is_audio_mime(f["mimeType"], f["name"])]
        self.listbox.delete(0, END)
        for (_id, name, mime) in self.search_results:
            self.listbox.insert(END, f"{name}   [{mime}]")

    def on_select_and_send_one(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um arquivo na lista.")
            return
        idx = sel[0]
        file_id = self.search_results[idx][0]
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                local_path = download_drive_file(file_id, self.svc, tmpdir)
                nome_desc = Path(local_path).stem
                upload_many([(local_path, nome_desc)], headless=False)
            messagebox.showinfo("Sucesso", "Upload concluído.")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha no envio do item selecionado: {e}")

    def on_select_and_send_all_from_list(self):
        if not self.search_results:
            messagebox.showwarning("Atenção", "A lista está vazia. Busque primeiro.")
            return
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                pairs = []
                for (fid, name, _mime) in self.search_results:
                    local_path = download_drive_file(fid, self.svc, tmpdir)
                    descricao = Path(local_path).stem
                    pairs.append((local_path, descricao))

                upload_many(pairs, headless=False)

            messagebox.showinfo("Sucesso", f"Uploads concluídos: {len(self.search_results)} arquivo(s).")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao enviar todos da lista: {e}")

# ===================== ENTRYPOINT =====================
if __name__ == "__main__":
    root = Tk()
    app = DrivePickerApp(root)
    root.mainloop()
