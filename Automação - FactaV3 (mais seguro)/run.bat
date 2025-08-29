@echo off
setlocal EnableExtensions

:: Diretório do script
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%"

:: Usa o Python do venv se existir; senão, cai no python do sistema
set "PYEXE=%SCRIPT_DIR%.venv311\Scripts\python.exe"
if not exist "%PYEXE%" set "PYEXE=python"

:: Parâmetros ou prompts
set "CODIGO_AF=%~1"
set "TWO_CAPTCHA_API_KEY=%~2"
set "USUARIO=%~3"
set "SENHA=%~4"

if "%CODIGO_AF%"=="" set /p CODIGO_AF=Informe CODIGO_AF: 
if "%TWO_CAPTCHA_API_KEY%"=="" set /p TWO_CAPTCHA_API_KEY=Informe TWO_CAPTCHA_API_KEY: 
if "%USUARIO%"=="" set /p USUARIO=Informe USUARIO (login/e-mail): 
if "%SENHA%"=="" (
  <nul set /p "=Informe SENHA (oculta): "
  for /f "usebackq delims=" %%i in (`
    powershell -NoProfile -Command ^
      "$p=Read-Host -AsSecureString; $b=[Runtime.InteropServices.Marshal]::SecureStringToBSTR($p);" ^
      "Write-Output ([Runtime.InteropServices.Marshal]::PtrToStringAuto($b))"
  `) do set "SENHA=%%i"
  echo.
)

:: Garante os browsers do Playwright para ESTE Python/venv
"%PYEXE%" -m playwright install chromium >nul 2>&1

:: Diagnóstico curto (sem heredoc)
"%PYEXE%" -c "import sys; print('PYTHON =', sys.executable)"
"%PYEXE%" -c "import importlib.util; m=importlib.util.find_spec('playwright'); print('PLAYWRIGHT =', getattr(m,'origin',None) or 'not installed')"

:: Executa seu script
"%PYEXE%" "%SCRIPT_DIR%main.py" -c "%CODIGO_AF%" -k "%TWO_CAPTCHA_API_KEY%" -u "%USUARIO%" -p "%SENHA%"
set "ERR=%ERRORLEVEL%"

echo(
if not "%ERR%"=="0" (
  echo [ERRO] main.py saiu com codigo %ERR%.
) else (
  echo [OK] Execucao concluida.
)
echo(
pause
popd
exit /b %ERR%

