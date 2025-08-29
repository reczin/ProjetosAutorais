@echo off
setlocal EnableExtensions

:: Diretório do script
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%"

:: Usa o Python do venv se existir; senão, cai no python do sistema
set "PYEXE=%SCRIPT_DIR%.venv311\Scripts\python.exe"
if not exist "%PYEXE%" set "PYEXE=%SCRIPT_DIR%.venv\Scripts\python.exe"
if not exist "%PYEXE%" set "PYEXE=python"

:: Parâmetros ou prompts
set "CODIGO_AF=%~1"
set "TWO_CAPTCHA_API_KEY=%~2"
set "USUARIO=%~3"
set "SENHA=%~4"
set "REPETIR=%~5"
set "VEZES=%~6"

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

:: Perguntas novas
if "%REPETIR%"=="" set /p REPETIR=Repetir? (1=sim, 2=nao): 
if "%REPETIR%"=="2" (
  set "VEZES=0"
) else (
  if "%VEZES%"=="" set /p VEZES=Quantas vezes vai repetir ^(int^):
)

:: Sanitiza VEZES (garante número inteiro >= 0)
echo %VEZES%| findstr /r "^[0-9][0-9]*$" >nul || (
  echo [AVISO] Valor inválido para VEZES. Usando 0.
  set "VEZES=0"
)

:: Garante os browsers do Playwright para ESTE Python/venv
"%PYEXE%" -m playwright install chromium >nul 2>&1

:: Diagnóstico curto
"%PYEXE%" -c "import sys; print('PYTHON =', sys.executable)"
"%PYEXE%" -c "import importlib.util; m=importlib.util.find_spec('playwright'); print('PLAYWRIGHT =', getattr(m,'origin',None) or 'not installed')"

:: Executa seu script com os novos flags -r e -v
"%PYEXE%" "%SCRIPT_DIR%main.py" ^
  -c "%CODIGO_AF%" ^
  -k "%TWO_CAPTCHA_API_KEY%" ^
  -u "%USUARIO%" ^
  -p "%SENHA%" ^
  -r "%REPETIR%" ^
  -v "%VEZES%"

set "ERR=%ERRORLEVEL%"

echo.
if not "%ERR%"=="0" (
  echo [ERRO] main.py saiu com codigo %ERR%.
) else (
  echo [OK] Execucao concluida.
)
echo.
pause
popd
exit /b %ERR%
