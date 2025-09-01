# 📖 Documentação da API – APIFacta

Esta documentação descreve os endpoints disponíveis na API **APIFacta**, que automatiza processos no sistema Facta utilizando **Playwright + 2Captcha**.

---

## 🔗 Base URL

- Localhost: `http://localhost:8000`  
- Servidor externo: `http://SEU_SERVIDOR:8000`  

---

## 📡 Endpoints

### 🔹 Health Check
**GET /AverbFacHealth**  
Verifica se a API está online.

**Exemplo request**
```bash
curl http://localhost:8000/AverbFacHealth
```

**Exemplo response**
```json
{ "ok": true }
```

---

### 🔹 Executar automação
**POST /AverbFacRun**  
Executa a automação de forma síncrona e retorna logs.

**Body (JSON)**
| Campo                | Tipo     | Obrigatório | Descrição |
|----------------------|----------|-------------|-----------|
| `CODIGO_AF`          | string   | ✅ | Código da AF |
| `TWO_CAPTCHA_API_KEY`| string   | ✅ | Chave de API do 2Captcha |
| `USUARIO`            | string   | ✅ | Login no sistema |
| `SENHA`              | string   | ✅ | Senha |
| `REPETIR`            | int      | ❌ | 1 = repetir, 2 = não |
| `VEZES`              | int      | ❌ | Número de repetições |
| `HEADLESS`           | boolean  | ❌ | Rodar navegador invisível |

**Exemplo request**
```bash
curl -X POST http://localhost:8000/AverbFacRun   -H "Content-Type: application/json"   -d '{
    "CODIGO_AF": "000000000",
    "TWO_CAPTCHA_API_KEY": "SUA_CHAVE",
    "USUARIO": "00000",
    "SENHA": "sua_senha",
    "REPETIR": 1,
    "VEZES": 1,
    "HEADLESS": true
  }'
```

**Exemplo response (sucesso)**
```json
{
  "jobId": "0f3f2d5e-81d3-4e7f-89b9-f1L5d1e4e5c2",
  "timestamp": "2025-09-01T18:30:00Z",
  "CODIGO_AF": "000000000",
  "USUARIO": "00000",
  "REPETIR": 1,
  "VEZES": 1,
  "HEADLESS": true,
  "status": "ok",
  "message": "Execução concluída com sucesso.",
  "log": "Inclusão efetuada com sucesso"
}
```

**Exemplo response (erro)**
```json
{
  "detail": {
    "jobId": "2c74c9e0-3f32-45l0-a8f9-d87e5b42bb3e",
    "timestamp": "2025-09-01T18:35:00Z",
    "CODIGO_AF": "000000000",
    "USUARIO": "00000",
    "status": "error",
    "message": "Chave 2Captcha inválida ou sem saldo",
    "log": ""
  }
}
```

---

### 🔹 Executar automação assíncrona
**POST /AverbFacRunAsync**  
Executa a automação em background.  

**Exemplo request**
```bash
curl -X POST http://localhost:8000/AverbFacRunAsync   -H "Content-Type: application/json"   -d '{"CODIGO_AF":"000000000","TWO_CAPTCHA_API_KEY":"SUA_CHAVE","USUARIO":"00000","SENHA":"sua_senha"}'
```

**Exemplo response**
```json
{ "jobId": "c3a12b9e", "status": "running" }
```

Consultar depois em `/AverbFacStatus/{jobId}`.

---

### 🔹 Último status
**GET /AverbFacStatus**  
Retorna o último job executado.

**Exemplo response**
```json
{
  "jobId": "c3a12b9e",
  "status": "ok",
  "message": "Inclusão efetuada com sucesso"
}
```

---

### 🔹 Status por Job ID
**GET /AverbFacStatus/{jobId}**  

**Exemplo request**
```bash
curl http://localhost:8000/AverbFacStatus/c3a12b9e
```

**Exemplo response**
```json
{
  "jobId": "c3a12b9e",
  "status": "finished",
  "message": "Inclusão efetuada com sucesso",
  "log": "Logs detalhados da execução"
}
```

---

### 🔹 Configuração atual
**GET /AverbFacConfig**  
Mostra os parâmetros usados na última execução.

**Exemplo response**
```json
{
  "CODIGO_AF": "000000000",
  "USUARIO": "00000",
  "REPETIR": 1,
  "VEZES": 1,
  "HEADLESS": true
}
```

---

### 🔹 Testar chave 2Captcha
**POST /AverbFacTestCaptcha**  
Valida se a chave da 2Captcha é válida e retorna o saldo.

**Exemplo request**
```bash
curl -X POST http://localhost:8000/AverbFacTestCaptcha   -H "Content-Type: application/json"   -d '{"api_key":"SUA_CHAVE"}'
```

**Exemplo response**
```json
{ "status": "ok", "balance": 12.5 }
```

---

### 🔹 Histórico de execuções
**GET /AverbFacHistory**  
Lista todas as execuções realizadas.

**Exemplo response**
```json
[
  {
    "jobId": "1a2b3c",
    "timestamp": "2025-09-01T18:30:00Z",
    "CODIGO_AF": "000000000",
    "status": "ok",
    "message": "Execução concluída com sucesso."
  },
  {
    "jobId": "4d5e6f",
    "timestamp": "2025-09-01T18:40:00Z",
    "CODIGO_AF": "000000000",
    "status": "error",
    "message": "Chave inválida 2Captcha"
  }
]
```

---

### 🔹 Histórico detalhado por Job ID
**GET /AverbFacHistory/{jobId}**  

**Exemplo request**
```bash
curl http://localhost:8000/AverbFacHistory/1a2b3c
```

**Exemplo response**
```json
{
  "jobId": "1a2b3c",
  "timestamp": "2025-09-01T18:30:00Z",
  "CODIGO_AF": "000000000",
  "USUARIO": "00000",
  "status": "ok",
  "message": "Execução concluída com sucesso.",
  "log": "Saída detalhada da automação"
}
```

---

## 📑 Observações

- O histórico atual é armazenado **em memória** (será limpo ao reiniciar o container).  
- É possível evoluir para persistência em **arquivo JSON** ou banco de dados.  
- A documentação automática da API está disponível em:  
  - Swagger UI → `/docs`  
  - Redoc → `/redoc`  

