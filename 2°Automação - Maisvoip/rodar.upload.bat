@echo off
REM Caminho para a Service Account (usa o mesmo diretório do .bat)
set "GOOGLE_APPLICATION_CREDENTIALS=%~dp0service-account.json"


REM Executa o script Python
python "%~dp0uploadaudio.py"

pause
