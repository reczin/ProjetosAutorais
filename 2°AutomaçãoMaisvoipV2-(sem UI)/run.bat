@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

REM --- Descobre diretório do script ---
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%"

REM --- Escolhe Python ---
set "PYEXE="
if exist ".venv\Scripts\python.exe" set "PYEXE=.venv\Scripts\python.exe"
if not defined PYEXE if exist ".venv311\Scripts\python.exe" set "PYEXE=.venv311\Scripts\python.exe"
if not defined PYEXE where py >nul 2>nul && set "PYEXE=py -3"
if not defined PYEXE where python >nul 2>nul && set "PYEXE=python"
if not defined PYEXE (
  echo [ERRO] Python nao encontrado. Instale Python 3.8+.
  goto :end
)

REM --- Instala dependencias ---
echo.
echo [INFO] Instalando dependencias (requirements.txt)...
%PYEXE% -m pip install -r requirements.txt
if errorlevel 1 (
  echo [AVISO] Falha ao instalar dependencias. Verifique o pip.
)

echo.
echo [INFO] Instalando navegadores do Playwright (chromium)...
%PYEXE% -m playwright install chromium

REM --- Confere service-account.json ---
if not exist "service-account.json" (
  echo [ERRO] Arquivo service-account.json nao encontrado na pasta atual.
  goto :end
)

REM --- Coleta dados: usa variaveis de ambiente se existirem, senao pergunta ---
set "IPBX_USER=%IPBX_USER%"
if not defined IPBX_USER set /p IPBX_USER=Usuario IPBX: 

set "IPBX_PASS=%IPBX_PASS%"
if not defined IPBX_PASS (
  set /p IPBX_PASS=Senha IPBX: 
)

set "IPBX_URL=%IPBX_URL%"
if not defined IPBX_URL set /p IPBX_URL=Base URL (ex: https://seu-dominio:8001/): 

set "DRIVE_FOLDER_ID=%DRIVE_FOLDER_ID%"
if not defined DRIVE_FOLDER_ID (
  set "ASK_DFID="
  set /p ASK_DFID=Informar DRIVE_FOLDER_ID (S/N)? 
  if /I "!ASK_DFID!"=="S" set /p DRIVE_FOLDER_ID=DRIVE_FOLDER_ID: 
)

echo.
echo [INFO] Deseja enviar TODOS os arquivos (1) ou apenas UM arquivo (0)?
set /p ALL_CHOICE=Digite 1 ou 0 [1]: 
if "!ALL_CHOICE!"=="" set "ALL_CHOICE=1"

set "FILENAME="
if /I "!ALL_CHOICE!"=="0" (
  set /p FILENAME=Nome exato do arquivo (inclua a extensao): 
)

echo.
echo [INFO] Rodar com janela (headless=0) ou sem janela (headless=1)?
set /p HEADLESS=Digite 0 ou 1 [0]: 
if "!HEADLESS!"=="" set "HEADLESS=0"

REM --- Monta comando ---
set "CMD=%PYEXE% uploader_patched.py --username "!IPBX_USER!" --password "!IPBX_PASS!" --base_url "!IPBX_URL!" --headless !HEADLESS! --all !ALL_CHOICE!"
if defined DRIVE_FOLDER_ID set "CMD=%CMD% --drive_folder_id "!DRIVE_FOLDER_ID!""
if /I "!ALL_CHOICE!"=="0" set "CMD=%CMD% --filename "!FILENAME!""

echo.
echo [INFO] Executando:
echo %CMD%
echo.

%CMD%
set "EXITCODE=%ERRORLEVEL%"

echo.
if "%EXITCODE%"=="0" (
  echo [OK] Finalizado com sucesso.
) else (
  echo [ERRO] Processo terminou com codigo %EXITCODE%.
)

:end
popd
pause