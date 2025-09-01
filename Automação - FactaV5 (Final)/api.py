import io
import sys
import uuid
import datetime
import asyncio
import requests
from fastapi import FastAPI, Body, HTTPException
from pydantic import BaseModel
from typing import Optional
import main as user_main  # fluxo principal da automação

app = FastAPI(title="APIFacta Automation API")

# ---------------------------
# Estruturas globais
# ---------------------------
HISTORY = []
LAST_STATUS = None

# ---------------------------
# Models
# ---------------------------
class RunPayload(BaseModel):
    CODIGO_AF: str
    TWO_CAPTCHA_API_KEY: str
    USUARIO: str
    SENHA: str
    REPETIR: Optional[int] = 1
    VEZES: Optional[int] = 1
    HEADLESS: Optional[bool] = True


# ---------------------------
# Helpers
# ---------------------------
def add_history(payload: dict, status: str, message: str, log: str = ""):
    job_id = str(uuid.uuid4())
    record = {
        "jobId": job_id,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "CODIGO_AF": payload.get("CODIGO_AF"),
        "USUARIO": payload.get("USUARIO"),
        "REPETIR": payload.get("REPETIR"),
        "VEZES": payload.get("VEZES"),
        "HEADLESS": payload.get("HEADLESS"),
        "status": status,
        "message": message,
        "log": log,
    }
    HISTORY.append(record)
    global LAST_STATUS
    LAST_STATUS = record
    return record


# ---------------------------
# Endpoints com prefixo AverbFac
# ---------------------------

@app.get("/AverbFacHealth")
def health():
    return {"ok": True}


@app.post("/AverbFacRun")
def run_task(payload: RunPayload = Body(...)):
    buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf
    try:
        user_main.CODIGO_AF = payload.CODIGO_AF
        user_main.TWO_CAPTCHA_API_KEY = payload.TWO_CAPTCHA_API_KEY
        user_main.USUARIO = payload.USUARIO
        user_main.SENHA = payload.SENHA
        user_main.REPETIR = payload.REPETIR
        user_main.VEZES = payload.VEZES
        user_main.main(headless=payload.HEADLESS, usuario=payload.USUARIO, senha=payload.SENHA)

        sys.stdout = old_stdout
        log_output = buf.getvalue()
        record = add_history(payload.dict(), "ok", "Execução concluída com sucesso.", log_output)
        return record
    except Exception as e:
        sys.stdout = old_stdout
        error_msg = str(e)
        record = add_history(payload.dict(), "error", error_msg)
        raise HTTPException(status_code=500, detail=record)


@app.post("/AverbFacRunAsync")
async def run_async(payload: RunPayload = Body(...)):
    job_id = str(uuid.uuid4())

    async def task():
        buf = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = buf
        try:
            user_main.CODIGO_AF = payload.CODIGO_AF
            user_main.TWO_CAPTCHA_API_KEY = payload.TWO_CAPTCHA_API_KEY
            user_main.USUARIO = payload.USUARIO
            user_main.SENHA = payload.SENHA
            user_main.REPETIR = payload.REPETIR
            user_main.VEZES = payload.VEZES
            user_main.main(headless=payload.HEADLESS, usuario=payload.USUARIO, senha=payload.SENHA)
            sys.stdout = old_stdout
            log_output = buf.getvalue()
            add_history(payload.dict(), "ok", "Execução concluída com sucesso.", log_output)
        except Exception as e:
            sys.stdout = old_stdout
            add_history(payload.dict(), "error", str(e))

    asyncio.create_task(task())
    return {"jobId": job_id, "status": "running"}


@app.get("/AverbFacStatus")
def get_status():
    if not LAST_STATUS:
        raise HTTPException(status_code=404, detail="Nenhuma execução encontrada")
    return LAST_STATUS


@app.get("/AverbFacStatus/{job_id}")
def get_status_job(job_id: str):
    for record in HISTORY:
        if record["jobId"] == job_id:
            return record
    raise HTTPException(status_code=404, detail="Job não encontrado")


@app.get("/AverbFacConfig")
def get_config():
    if not LAST_STATUS:
        return {"message": "Nenhuma execução ainda."}
    cfg = {k: LAST_STATUS[k] for k in ["CODIGO_AF", "USUARIO", "REPETIR", "VEZES", "HEADLESS"]}
    return cfg


@app.post("/AverbFacTestCaptcha")
def test_captcha(api_key: str = Body(..., embed=True)):
    url = "https://api.2captcha.com/getBalance"
    try:
        resp = requests.post(url, json={"clientKey": api_key}, timeout=20)
        data = resp.json()
        if data.get("errorId") == 0:
            return {"status": "ok", "balance": data.get("balance")}
        else:
            return {"status": "error", "message": data.get("errorDescription", "Erro desconhecido")}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})


@app.get("/AverbFacHistory")
def get_history():
    return HISTORY


@app.get("/AverbFacHistory/{job_id}")
def get_history_item(job_id: str):
    for record in HISTORY:
        if record["jobId"] == job_id:
            return record
    raise HTTPException(status_code=404, detail="Job não encontrado")
