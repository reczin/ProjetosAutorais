import os
import json
from typing import Optional
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field

import main as user_main


class RunPayload(BaseModel):
    CODIGO_AF: str = Field(..., description="Código AF")
    TWO_CAPTCHA_API_KEY: str = Field(..., description="Chave 2Captcha")
    USUARIO: str = Field(..., description="Usuário/login")
    SENHA: str = Field(..., description="Senha")
    REPETIR: Optional[int] = Field(default=1, description="1 para repetir, 2 para não")
    VEZES: Optional[int] = Field(default=1, description="Quantidade de repetições se REPETIR=1")
    HEADLESS: Optional[bool] = Field(default=True, description="Executar navegador em modo headless")


app = FastAPI(title="Runner API", version="1.0.0")


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/run")
def run_task(payload: RunPayload = Body(...)):
    """
    Executa o fluxo principal de forma síncrona.
    n8n pode chamar este endpoint via HTTP Request node (POST JSON).
    """
    try:
        os.environ["CODIGO_AF"] = payload.CODIGO_AF
        os.environ["TWO_CAPTCHA_API_KEY"] = payload.TWO_CAPTCHA_API_KEY
        os.environ["USUARIO"] = payload.USUARIO
        os.environ["SENHA"] = payload.SENHA
        os.environ["REPETIR"] = str(payload.REPETIR if payload.REPETIR is not None else 1)
        os.environ["VEZES"] = str(payload.VEZES if payload.VEZES is not None else 1)

        user_main.main(
            headless=bool(payload.HEADLESS),
            usuario=payload.USUARIO,
            senha=payload.SENHA
        )

        return {"status": "ok", "message": "Execução concluída com sucesso."}

    except Exception as e:

        raise HTTPException(status_code=500, detail={"error": str(e)})
