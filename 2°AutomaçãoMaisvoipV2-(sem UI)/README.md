# Uploader de Áudios (Google Drive → IPBX)

Automatiza o **download de áudios do Google Drive** (via **Service Account**) e o **upload para o IPBX** (via **Playwright**).  
Compatível com Python **3.8+** (recomendado **3.10+**).

---

## 📁 Estrutura esperada
```
/seu-projeto
├─ README.md
├─ run.bat
├─ requirements.txt
├─ service-account.json      # credencial do Google (Service Account) + opcional drive_folder_id
├─ uploader_patched.py       # script principal
└─ downloads/                # (gerada automaticamente) arquivos baixados do Drive
```

> **Nota:** O script lê o `drive_folder_id` nesta ordem de prioridade:
1. `--drive_folder_id` (CLI)
2. Variável de ambiente `DRIVE_FOLDER_ID`
3. Campo `drive_folder_id` dentro do `service-account.json`

---

## 🔧 Requisitos
- **Python 3.8+** instalado (Windows: `py -3 --version`)
- **Google Drive API** habilitada no projeto da Service Account
- A **pasta do Drive** deve estar **compartilhada com o e‑mail da Service Account**
- Conectividade para baixar o **Chromium do Playwright** na primeira execução

### Instalar dependências
```bash
pip install -r requirements.txt
playwright install chromium
```

> Se estiver usando virtualenv:
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

---

## 🔐 Configuração do `service-account.json`
1. Crie uma **Service Account** no Google Cloud e **baixe a chave JSON**.
2. **Compartilhe a pasta do Drive** (My Drive ou Shared Drive) com o **e‑mail** da Service Account (permissão de leitor é suficiente).
3. Opcionalmente, adicione `"drive_folder_id": "<ID-DA-PASTA>"` ao JSON para facilitar.
4. Salve o arquivo como `service-account.json` na raiz do projeto.

> Em Shared Drives, o script já usa `supportsAllDrives=True` e `includeItemsFromAllDrives=True`.

---

## ▶️ Como usar (direto no Python)
Enviar **todos** os áudios da pasta (interface visível, headless off):
```bash
python uploader_patched.py --username "SEU_LOGIN" --password "SUA_SENHA" --headless 0 --base_url "https://SEU-IPBX:8001/"
```

Enviar **apenas um arquivo** específico:
```bash
python uploader_patched.py --username "SEU_LOGIN" --password "SUA_SENHA" --all 0 --filename "Teste.mp3" --headless 0 --base_url "https://SEU-IPBX:8001/"
```

### Parâmetros principais
- `--username` / `--password` → credenciais do IPBX (obrigatório)
- `--base_url` → URL de login do IPBX (`https://host:porta/`). Ex.: `https://seu-dominio:8001/`
- `--service_account` → caminho do JSON (padrão: `service-account.json`)
- `--drive_folder_id` → ID da pasta (se não usar variável/JSON)
- `--download_dir` → pasta local para salvar áudios (padrão: `downloads`)
- `--allowed_ext` → extensões aceitas quando `--all=1` (padrão: `mp3,wav,ogg`)
- `--all` → `1` (todos) ou `0` (apenas `--filename`)
- `--filename` → necessário quando `--all=0`
- `--headless` → `1` (sem janela) ou `0` (com janela)

> O script ignora erros HTTPS (`ignore_https_errors=True`) para suportar certificados self‑signed.

---

## 🖱️ Uso com `run.bat`
O `run.bat` prepara o ambiente e executa o script, aceitando **variáveis de ambiente** para pular perguntas:

- `IPBX_USER` → usuário do IPBX
- `IPBX_PASS` → senha do IPBX
- `IPBX_URL`  → base_url do IPBX (ex.: `https://seu-dominio:8001/`)
- `DRIVE_FOLDER_ID` → ID da pasta no Drive (opcional se já vier no JSON)

**Exemplo (PowerShell):**
```powershell
$env:IPBX_USER="operador@empresa"
$env:IPBX_PASS="minha-senha"
$env:IPBX_URL="https://seu-dominio:8001/"
.\run.bat
```

Se as variáveis não estiverem definidas, o `.bat` perguntará de forma interativa (com opção de enviar todos os arquivos ou um arquivo específico).

---

## ❗ Dicas & Solução de Problemas

- **Timeout ao baixar Chromium**  
  Rede corporativa pode bloquear o download. Tente:
  ```bash
  playwright install chromium
  ```
  ou verifique proxy/firewall.

- **Falha de login / seletores mudaram**  
  O script tenta diferentes seletores (por `role`, `placeholder` e `css`) e aguarda a navegação.  
  Se o seu IPBX tiver rótulos muito específicos, ajuste os regex/seletores em `login_and_navigate` e `upload_one_file`.

- **Service Account sem acesso**  
  Garanta que a pasta do Drive esteja **compartilhada** com o e‑mail da service account e que o `drive_folder_id` esteja correto.

- **Segurança**  
  Não commite `service-account.json` em repositórios públicos. Trate credenciais como segredo.

---

## 🧾 Licença
Uso interno/privado. Adapte conforme sua política.
Automação criada por Roger Eduardo Corrêa©
Duvidas sobre rec.regor@gmail.com