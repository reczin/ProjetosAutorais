# 🚀 APIFactaV5 – Automação com Playwright + 2Captcha

Automação que acessa o sistema **Facta**, utilizando **Playwright (Chromium)** para navegação automatizada e **2Captcha** para resolução de reCAPTCHA.  
A automação é exposta como **API HTTP** via **FastAPI**, permitindo integração direta com sistemas de orquestração (como **n8n**).

---

## 📖 Como funciona

1. O usuário envia um `POST` para a API com as credenciais e parâmetros necessários (`CODIGO_AF`, `USUARIO`, `SENHA`, etc.).  
2. O **Playwright** abre o navegador (em modo headless ou não), acessa o sistema e executa o fluxo definido em `main.py`.  
3. O **2Captcha** resolve o reCAPTCHA quando necessário.  
4. Os logs de execução são capturados e retornados na resposta.  
5. Todas as execuções ficam salvas em **histórico**, acessível via endpoints `/AverbFacHistory` e `/AverbFacHistory/{jobId}`.  

---

## ⚙️ Instruções de uso

### 1. Rodando na própria máquina (sem Docker)

Pré-requisitos:
- Python 3.11+
- Node.js (para suporte ao Playwright)
- Google Chrome ou navegadores suportados

Instalação:
```bash
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows PowerShell

pip install -r requirements.txt
playwright install --with-deps
```

Execução da API:
```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

---

### 2. Rodando em localhost com Docker

Buildar imagem da automação:
```bash
docker compose -f docker-compose.api.yml build
```

Subir container:
```bash
docker compose -f docker-compose.api.yml up -d
```

Testar saúde:
```bash
curl http://localhost:8000/AverbFacHealth
```

---

### 3. Rodando em servidor externo

No servidor Linux (com Docker instalado):

```bash
git clone https://github.com/SEU_USUARIO/APIFactaV5.git
cd APIFactaV5
docker compose -f docker-compose.api.yml up -d --build
```

Depois, acesse a API externamente via IP do servidor:
```
http://SEU_SERVIDOR:8000/AverbFacHealth
```

⚠️ Recomendado: usar **NGINX + HTTPS (Let's Encrypt)** ou rodar atrás de um **API Gateway**.

---

## 📡 Endpoints principais

### 🔹 Health
`GET /AverbFacHealth`  
Verifica se a API está online.

---

### 🔹 Executar automação
`POST /AverbFacRun`

Exemplo:
```bash
curl -X POST http://localhost:8000/AverbFacRun   -H "Content-Type: application/json"   -d '{
    "CODIGO_AF": "103281902",
    "TWO_CAPTCHA_API_KEY": "SUA_CHAVE_2CAPTCHA",
    "USUARIO": "97028",
    "SENHA": "sua_senha",
    "REPETIR": 1,
    "VEZES": 1,
    "HEADLESS": true
  }'
```

---

### 🔹 Histórico
- `GET /AverbFacHistory` → lista execuções  
- `GET /AverbFacHistory/{jobId}` → detalhes de uma execução  

---

### 🔹 Status
- `GET /AverbFacStatus` → último job executado  
- `GET /AverbFacStatus/{jobId}` → status detalhado por job  

---

### 🔹 Config
`GET /AverbFacConfig` → mostra os parâmetros da última execução  

---

### 🔹 Teste de chave 2Captcha
`POST /AverbFacTestCaptcha`

Exemplo:
```bash
curl -X POST http://localhost:8000/AverbFacTestCaptcha   -H "Content-Type: application/json"   -d '{"api_key":"SUA_CHAVE"}'
```

---

## 🔄 Uso no n8n

Adicione um nó **HTTP Request**:
- **Method:** `POST`  
- **URL:** `http://SEU_SERVIDOR:8000/AverbFacRun`  
- **Headers:** `Content-Type: application/json`  
- **Body:** JSON
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

A saída conterá:
- `status` → ok/error  
- `jobId` → identificador único  
- `log` → saída detalhada  

---

## 🔗 Documentação automática

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)  
- Redoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)  

---

## 📑 Licença

Uso interno exclusivo.  
Automação desenvolvida por:

**Roger Eduardo Corrêa**  
📧 [rec.regor@gmail.com](mailto:rec.regor@gmail.com)
