# APIFacta – Automação Playwright + 2Captcha (CLI e API p/ n8n)

Este projeto automatiza tarefas no sistema Facta usando **Playwright (Chromium)** e resolve **reCAPTCHA v2 / Enterprise** via **2Captcha**.  
Você pode rodar de duas formas:

1) **Modo CLI (batch)** – executa e finaliza  
2) **Modo API HTTP (para n8n)** – o container fica de pé e você dispara via `POST /run`


---

## Sumário
- [Pré-requisitos](#pré-requisitos)
- [Instalação local (Windows)](#instalação-local-windows)
- [Como executar (CLI)](#como-executar-cli)
- [Como executar (API HTTP p-n8n)](#como-executar-api-http-pn8n)
- [Docker (CLI)](#docker-cli)
- [Docker (API HTTP p-n8n)](#docker-api-http-pn8n)
- [Estrutura de variáveis](#estrutura-de-variáveis)
- [n8n – Exemplo de chamada](#n8n--exemplo-de-chamada)
- [Boas práticas e segurança](#boas-práticas-e-segurança)
- [Troubleshooting](#troubleshooting)

---

## Pré-requisitos

- **Windows + PowerShell/CMD** (ou WSL)
- **Python 3.11+**
- **Playwright** com Chromium instalado: `python -m playwright install chromium`
- Dependências Python listadas em `requirements.txt`

> Observação: em Docker, tudo isso já é preparado na imagem.

---

## Instalação local (Windows)

Crie e ative um ambiente virtual (opcional, recomendado):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale as dependências e o navegador do Playwright:
```powershell
pip install --upgrade pip
pip install -r requirements.txt
python -m playwright install chromium
```

---

## Como executar (CLI)

O script aceita parâmetros por **linha de comando**, **variáveis de ambiente** ou **prompts interativos** (fallback).

### Opção A — Parâmetros (recomendado)
```powershell
python .\main.py -c CODIGO_AF -k SUA_CHAVE_2CAPTCHA -u SEU_LOGIN -p SUA_SENHA -r 1 -v 1
```

### Opção B — Variáveis de ambiente
```powershell
$env:CODIGO_AF="CODIGO_AF"
$env:TWO_CAPTCHA_API_KEY="SUA_CHAVE_2CAPTCHA"
$env:USUARIO="SEU_LOGIN"
$env:SENHA="SUA_SENHA"
$env:REPETIR="1"
$env:VEZES="1"
python .\main.py
```

### Opção C — Interativo (fallback)
```powershell
python .\main.py
# O script pedirá os dados que faltarem (sem exibir a senha em claro).
```

### Headless
Para rodar sem interface gráfica (headless), deixe assim na chamada principal do script (ou torne-o configurável por variável, se preferir):
```python
main(headless=True, usuario=USUARIO, senha=SENHA)
```

---

## Como executar (API HTTP p/ n8n)

Você pode expor um endpoint HTTP e passar os parâmetros via JSON. Há duas abordagens:

1. **`api.py`** (arquivo separado de API) – recomendado para manter o `main.py` limpo.  
2. **Transformar o `main.py` em servidor** – alternativa se quiser um único ponto de entrada.

O repositório inclui a opção **`api.py`**. Com ela, suba localmente:

```powershell
pip install fastapi uvicorn
uvicorn api:app --host 0.0.0.0 --port 8000
```

Teste saúde:
```powershell
curl http://localhost:8000/health
# {"ok": true}
```

Dispare a execução:
```powershell
curl -X POST "http://localhost:8000/run" ^
  -H "Content-Type: application/json" ^
  -d "{""CODIGO_AF"":""103281902"",""TWO_CAPTCHA_API_KEY"":""SUA_CHAVE"",""USUARIO"":""SEU_LOGIN"",""SENHA"":""SUA_SENHA"",""REPETIR"":1,""VEZES"":1,""HEADLESS"":true}"
```

> A rota `/run` executa **síncrono**: a requisição fica aberta até o Playwright terminar. Ajuste o timeout do seu cliente/n8n se necessário.

---

## Docker (CLI)

Este modo roda o script diretamente e encerra ao finalizar.

### Build
```bash
docker compose build
```

### Run
```bash
# usando .env (crie a partir de .env.example e preencha os valores)
docker compose up --build
# ou rodar em background
docker compose up -d
```

> Para rodar headless, você pode manter o `main(headless=True)` no código.  
> Se usar modo não-headless, considere rodar sob `Xvfb` (já tratado no Dockerfile original).

---

## Docker (API HTTP p/ n8n)

Este modo sobe um **servidor HTTP** dentro do container, exposto na porta **8000**.

### Build & Up
```bash
docker compose -f docker-compose.api.yml up --build -d
```

### Teste saúde
```bash
curl http://localhost:8000/health
```

### Disparar execução
```bash
curl -X POST http://localhost:8000/run   -H "Content-Type: application/json"   -d '{"CODIGO_AF":"103281902","TWO_CAPTCHA_API_KEY":"SUA_CHAVE","USUARIO":"SEU_LOGIN","SENHA":"SUA_SENHA","REPETIR":1,"VEZES":1,"HEADLESS":true}'
```

> Se quiser salvar arquivos baixados no host, mapeie volume no `docker-compose.api.yml`:
```yaml
services:
  apifacta_api:
    volumes:
      - ./downloads:/app/downloads
```
E aponte os caminhos de download/salvamento no código para `/app/downloads`.

---

## Estrutura de variáveis

Chaves esperadas (via args/env/body JSON):

- `CODIGO_AF` — código da AF a ser processada  
- `TWO_CAPTCHA_API_KEY` — chave da API 2Captcha  
- `USUARIO` — login/e‑mail no site  
- `SENHA` — senha do site  
- `REPETIR` — `1` (sim) ou `2` (não)  
- `VEZES` — inteiro (quantidade de repetições se `REPETIR=1`)  
- `HEADLESS` — `true`/`false` (apenas na API)

---

## n8n – Exemplo de chamada

No **HTTP Request node**:
- **Method:** `POST`
- **URL:** `http://SEU_HOST:8000/run`
- **Headers:** `Content-Type: application/json`
- **Body:** JSON (pode vir de nós anteriores)
```json
{
  "CODIGO_AF": "{{$json.CODIGO_AF}}",
  "TWO_CAPTCHA_API_KEY": "{{$json.TWO_CAPTCHA_API_KEY}}",
  "USUARIO": "{{$json.USUARIO}}",
  "SENHA": "{{$json.SENHA}}",
  "REPETIR": {{$json.REPETIR || 1}},
  "VEZES": {{$json.VEZES || 1}},
  "HEADLESS": {{$json.HEADLESS ?? true}}
}
```

> Ajuste o **Timeout** do node conforme a duração do fluxo. A rota é síncrona.

---

## Boas práticas e segurança

- **Nunca** versionar credenciais. Use `.env` local (modo CLI) ou variáveis seguras/orquestrador (n8n) no modo API.
- Prefira **headless** em servidores; se o site bloquear headless, use modo com UI (Docker pode usar Xvfb).
- Para expor a API:
  - Proteja com **rede** (firewall/VPN) e/ou **auth** no gateway (reverso/ingress).
  - Se precisar, adicione validação de token na API (ex.: header `X-API-Key`).

---

## Troubleshooting

- **2Captcha erro**: verifique saldo e chave (`TWO_CAPTCHA_API_KEY`).
- **`net::ERR_ABORTED` / timeouts**: há retry no `safe_goto`; verifique a rede do host/container.
- **Cabeçalhos/antibot**: se notar bloqueio, teste `headless=False` (API: `HEADLESS: false`) e aumente `wait_for_*`.
- **Memória compartilhada do Chromium em Docker**: adicione `shm_size: "1gb"` no compose se páginas forem pesadas.
- **Downloads não aparecem no host**: mapeie volume e salve em `/app/downloads`.

---

## Licença

Uso interno.
Automação feita por Roger Eduardo Corrêa©, eventuais duvidas rec.regor@gmail.com

