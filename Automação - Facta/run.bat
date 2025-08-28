@echo off
setlocal
cd /d "%~dp0"

REM Ativa o venv existente
call .venv311\Scripts\activate.bat

REM Instala dependências se necessário (checagem leve)
python -m pip show playwright >nul 2>&1 || python -m pip install -r requirements.txt
python -m playwright install chromium >nul 2>&1

REM Uso: run.bat [CODIGO_AF] [TWO_CAPTCHA_API_KEY]
if "%~1"=="" (
  set /p CODIGO_AF=Informe CODIGO_AF: 
) else (
  set "CODIGO_AF=%~1"
)

if "%~2"=="" (
  set /p TWO_CAPTCHA_API_KEY=Informe TWO_CAPTCHA_API_KEY: 
) else (
  set "TWO_CAPTCHA_API_KEY=%~2"
)

python main.py --codigo-af "%CODIGO_AF%" --captcha-key "%TWO_CAPTCHA_API_KEY%"
endlocal
