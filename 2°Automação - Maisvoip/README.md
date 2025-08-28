# Upload de Áudio (Google Drive → MaisVoIP) com Playwright

Interface simples (Tkinter) para **buscar áudios no Google Drive** e **enviar para o painel do MaisVoIP Discador** em **IPBX → Funcionalidades → Áudio**, automatizando o processo com **Playwright**.

> Este README cobre o script `uploadaudio.py` e o uso de uma **Service Account** do Google. Há também um atalho opcional `rodar.upload.bat` para execução em 1 clique no Windows.

---

## 📁 Estrutura

- `uploadaudio.py` — App com GUI (Tkinter) que:
  - Autentica no Google Drive via **Service Account** (escopo somente leitura);
  - Permite **colar um link/ID** de arquivo ou **pasta** do Drive;
  - Faz **download** local dos áudios e envia todos/um por vez;
  - Abre o MaisVoIP (**login**, **IPBX → Funcionalidades → Áudio**) e **anexa** cada arquivo.
- `service-account.json` — credenciais da Service Account (MANTER FORA DO GIT).
- `rodar.upload.bat` — (opcional) script para ativar o venv, setar a variável de ambiente e executar o app.

> Observação: mantenha `service-account.json` fora do controle de versão e use variável de ambiente `GOOGLE_APPLICATION_CREDENTIALS` para apontar o caminho do arquivo.

---

## ✅ Pré‑requisitos

- **Python 3.10+** (recomendado 3.11)
- Pacotes Python:
  - `playwright`
  - `google-api-python-client`
  - `google-auth`
  - `google-auth-httplib2`
- Navegadores do Playwright instalados
- Acesso ao painel do **MaisVoIP Discador** (URL, usuário e senha ativos)

---

## 🚀 Instalação Rápida

```bash
# 1) Criar e ativar o ambiente
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 2) Instalar dependências
pip install playwright google-api-python-client google-auth google-auth-httplib2

# 3) Instalar navegadores do Playwright
python -m playwright install
```

> Se houver SSL não confiável no domínio (ex.: :8001 com certificado interno), avalie usar `ignore_https_errors=True` ao criar o contexto do Playwright (ajuste no código conforme sua política de segurança).

---

## 🔧 Configuração

### 1) Google Service Account
- Guarde o arquivo **`service-account.json`** em um local seguro (fora do repositório).
- Defina a variável de ambiente **`GOOGLE_APPLICATION_CREDENTIALS`** apontando para esse caminho.

**Windows (cmd/powershell, sessão atual):**
```bat
set GOOGLE_APPLICATION_CREDENTIALS=C:\caminho\para\service-account.json
```

**macOS/Linux (bash/zsh):**
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/caminho/para/service-account.json
```

> O script valida essa variável no início; se não estiver definida, aborta com instrução clara para corrigir.

### 2) Credenciais do MaisVoIP
O script possui constantes para **URL**, **usuário** e **senha**. Recomenda-se substituir por **variáveis de ambiente** para produção:

Variáveis sugeridas:
- `MAISVOIP_URL` (ex.: `https://seu.dominio:8001/maisvoip/autenticacao.php`)
- `MAISVOIP_USER`
- `MAISVOIP_PASS`

> Ajuste o código para ler via `os.getenv(...)` ou utilize um gerenciador de segredos. Não deixe credenciais hardcoded em produção.

---

## ▶️ Uso

### Executar pela linha de comando
Com o ambiente ativado e `GOOGLE_APPLICATION_CREDENTIALS` configurada:

```bash
python uploadaudio.py
```

A interface abrirá com três formas de envio:
1. **Colar link/ID** (arquivo ou pasta) do Google Drive e clicar em **“Baixar & Enviar (1)”** (envia 1 arquivo);
2. **Colar link/ID de PASTA** e clicar em **“Enviar TODOS da pasta”** (envia todos os áudios da pasta);
3. **Pesquisar pelo nome**: digite um termo, clique **“Buscar”**, selecione na lista e use:
   - **“Selecionar & Enviar (1)”** (envio de um arquivo);
   - **“Selecionar & Enviar TODOS (lista)”** (envia todos os resultados listados).

### Executar com `rodar.upload.bat` (Windows)
Dê **duplo clique** no arquivo para automatizar a ativação do venv e a execução do app.
Se precisar de um modelo, este é um **exemplo** que você pode adaptar ao seu ambiente:

```bat
@echo off
REM Ativar venv
call .venv\Scripts\activate

REM Apontar a Service Account
set GOOGLE_APPLICATION_CREDENTIALS=%~dp0service-account.json

REM Executar
python uploadaudio.py
pause
```

> Se o seu `rodar.upload.bat` já estiver configurado, use-o diretamente. O exemplo acima é apenas um template.

---

## 🎧 Formatos de Áudio Suportados

O script detecta automaticamente áudios por **MIME** e, como fallback, pela **extensão**. Formatos aceitos incluem:
`mp3, wav, ogg, m4a, aac, flac, wma, amr, gsm, g729`.

> Arquivos **Google Docs** (Sheets/Docs/Slides) **não** são tratados como áudio; se enviados, são exportados (PDF/CSV/etc.) — não úteis para upload de áudio no painel.

---

## 🧭 Fluxo automatizado (resumo)

1. Autentica no **Google Drive** (Service Account, escopo leitura);
2. Faz **download** temporário dos arquivos de áudio selecionados;
3. Abre o navegador com **Playwright** → **MaisVoIP** → **IPBX → Funcionalidades → Áudio**;
4. Para **cada arquivo**:
   - Abre o formulário **Inserir**;
   - Seleciona **origem Upload**;
   - **Anexa** o arquivo e define a **descrição** (nome do arquivo);
   - **Salva** e retorna para a lista;
5. Fecha o navegador ao final.

---

## 🛠️ Dicas de Depuração

- **“Defina a variável de ambiente GOOGLE_APPLICATION_CREDENTIALS…”**  
  → Configure a variável apontando para o `service-account.json` (ver seção Configuração).
- **Time‑outs/Seletores**  
  → Aumente `context.set_default_timeout(...)`; valide nomes dos botões (*“Inserir”, “Salvar”*) e o **iframe** (`name="Post"`).
- **Headless vs Headful**  
  → Em caso de erro visual, rode com janela visível (o script já usa `headless=False` nos envios da interface).
- **Captcha/2FA**  
  → Se houver mecanismos anti‑bot, pode ser necessário intervir manualmente ou ajustar a estratégia de login.
- **SSL corporativo**  
  → Ajuste o contexto para ignorar erros de certificado **apenas** se aprovado internamente.

---

## 🔐 Segurança (essencial)

- Mantenha `service-account.json` **fora** do Git e com permissões restritas.
- Use escopos mínimos no Google Cloud (apenas `drive.readonly`).
- Não armazene credenciais do painel **em texto plano**; prefira variáveis de ambiente/secret manager.
- Rotacione chaves periodicamente e monitore acessos.

**Sugestão de `.gitignore`:**
```
.venv/
*.pyc
__pycache__/
service-account.json
.env
```

---

## 📜 Licença

Uso interno. Adapte conforme sua necessidade. Automação Criada por Roger Eduardo Corrêa© Eventuais duvidas rec.regor@gmail.com

---

## 📣 Créditos & Referências

- Google Drive API (Service Accounts)
- Playwright for Python
- MaisVoIP Discador — IPBX → Funcionalidades → Áudio
