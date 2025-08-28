# APIFacta V2 — Playwright + 2Captcha

Automação em **Playwright** para o fluxo do sistema Facta, com resolução automática de **reCAPTCHA v2 / Enterprise** via **2Captcha**. Entrada dinâmica de `CODIGO_AF` e `TWO_CAPTCHA_API_KEY` por **parâmetros**, **variáveis de ambiente** ou **prompt interativo** (fallback). A lógica de navegação usa *auto‑wait* e `safe_goto` com *retry* para evitar `net::ERR_ABORTED` no pós‑login. (ver `main.py`) 

> O script lê os argumentos `--codigo-af` e `--captcha-key`, e também aceita `CODIGO_AF` / `TWO_CAPTCHA_API_KEY` via env.  fileciteturn6file0  
> Dependências listadas em `requirements.txt`.  fileciteturn6file1

---

## Requisitos

- Windows (PowerShell/CMD)
- Python **3.11** (o projeto usa `.venv311` já criado)
- Navegador Playwright Chromium instalado via `python -m playwright install chromium`

## Instalação (primeira vez)

Abra o **PowerShell** na pasta do projeto e ative o venv existente:

```powershell
.\.venv311\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m playwright install chromium
```

> Se der erro de política ao ativar o venv:  
> `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` e tente ativar de novo.

---

## Como executar

Você pode passar os parâmetros **na linha de comando**, **via variáveis de ambiente**, ou **interativo** (o script pergunta).

### A) Parâmetros (recomendado)
```powershell
.\.venv311\Scripts\Activate.ps1
python .\main.py -c CODIGO_AF -k SUA_CHAVE_2CAPTCHA
```

### B) Variáveis de ambiente (sessão atual)
```powershell
.\.venv311\Scripts\Activate.ps1
$env:CODIGO_AF="CODIGO_AF"
$env:TWO_CAPTCHA_API_KEY="SUA_CHAVE_2CAPTCHA"
python .\main.py
```

### C) Interativo
```powershell
.\.venv311\Scripts\Activate.ps1
python .\main.py
# → Informe CODIGO_AF: ...
# → Informe TWO_CAPTCHA_API_KEY: ...
```

### D) Via `run.bat`
- Com argumentos: `run.bat XXXXXXXXX XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX`  
- Sem argumentos: o `.bat` pergunta e repassa para o Python.

---

## Estrutura e pontos-chave

- `main.py`
  - Pós‑login estável com `wait_for_load_state("networkidle")` (evita navegações concorrentes).  fileciteturn6file0
  - `safe_goto(page, url)` com *retry* em `net::ERR_ABORTED`.  fileciteturn6file0
  - Integração 2Captcha via `createTask` / `getTaskResult` e injeção do token em `g-recaptcha-response`.  fileciteturn6file0
  - Entrada dinâmica de `CODIGO_AF` e `TWO_CAPTCHA_API_KEY` por `argparse`/env/prompt.  fileciteturn6file0

- `requirements.txt`
  - `playwright>=1.45`
  - `requests>=2.31`  fileciteturn6file1

---

## Dicas / Troubleshooting

- **`ERROR_KEY_DOES_NOT_EXIST` (2Captcha)**  
  A chave enviada está faltando/errada. Repassar `-k` ou setar `TWO_CAPTCHA_API_KEY` corretamente.

- **`net::ERR_ABORTED` no `goto`**  
  O `safe_goto` já tenta novamente; garanta que o login terminou (o script espera `networkidle`).  fileciteturn6file0

- **Execução em produção (headless)**  
  O `main()` está `headless=False`. Se quiser headless, ajuste no final do arquivo para `main(headless=True)`.  fileciteturn6file0

- **Playwright browsers**  
  Se mudar de máquina/usuário, rode `python -m playwright install chromium` para instalar o runtime do navegador.

---

## Segurança

- **NÃO** deixe sua chave do 2Captcha em arquivos versionados.  
- Prefira passar por **argumento** (`-k`) ou via **variável de ambiente**.  
- Evite subir `run.bat` com a chave escrita em texto plano.

---

## Licença

Uso interno.
Automação feita por Roger Eduardo Corrêa©.
eventuais duvidas:
@rec.regor@gmail.com
