@echo off
setlocal ENABLEDELAYEDEXPANSION

REM ============================
REM Sistema Inventario - Manager
REM Windows CMD helper
REM ============================

set VENV=.venv
set PY=python
set PIP=pip
set BACKEND=backend
set PORT=8000
set HOST=127.0.0.1

if exist .env (
  for /f "usebackq tokens=1,2 delims==" %%A in (".env") do (
    if /I "%%A"==PORT set PORT=%%B
    if /I "%%A"==HOST set HOST=%%B
  )
)

if not exist %VENV% (
  echo ℹ️ Creando entorno virtual...
  %PY% -m venv %VENV%
  if errorlevel 1 (
    echo ❌ No se pudo crear el entorno virtual. Asegure que Python esta instalado y en PATH.
    exit /b 1
  )
)

set ACTIVATE=%VENV%\Scripts\activate
if not exist %ACTIVATE% (
  echo ❌ No se encontro el activador del entorno: %ACTIVATE%
  exit /b 1
)

call %ACTIVATE%

if not exist %VENV%\_installed ( 
  echo ℹ️ Instalando dependencias...
  %PIP% install --upgrade pip
  %PIP% install -r requirements.txt
  if errorlevel 1 (
    echo ❌ Fallo instalando dependencias.
    exit /b 1
  )
  echo done> %VENV%\_installed
)

if not exist %BACKEND%\uploaded_evidencias mkdir %BACKEND%\uploaded_evidencias

if "%1"=="setup" goto :setup
if "%1"=="dev" goto :dev
if "%1"=="run" goto :run
if "%1"=="status" goto :status
if "%1"=="clean" goto :clean
if "%1"=="backup" goto :backup
if "%1"=="test" goto :test
if "%1"=="help" goto :help

goto :help

:setup
  echo ✅ Proyecto configurado. Para iniciar: manage.cmd dev
  goto :eof

:dev
  echo 🚀 Iniciando servidor desarrollo en http://%HOST%:%PORT%
  cd %BACKEND%
  uvicorn app:app --host %HOST% --port %PORT%
  goto :eof

:run
  echo 🚀 Iniciando servidor produccion en http://%HOST%:%PORT%
  cd %BACKEND%
  uvicorn app:app --host %HOST% --port %PORT%
  goto :eof

:status
  echo 📊 Estado del proyecto
  if exist %VENV% (echo   ✅ Entorno virtual) else (echo   ❌ Sin entorno virtual)
  if exist %BACKEND%\app.py (echo   ✅ Backend) else (echo   ❌ Falta backend/app.py)
  if exist frontend\admin.html (echo   ✅ Frontend) else (echo   ❌ Falta frontend/admin.html)
  if exist backend\inventario_evidencias.db (echo   ✅ DB evidencias) else (echo   ⚠️  Sin DB evidencias aun)
  goto :eof

:clean
  echo 🧹 Limpiando temporales...
  for /r %%i in (__pycache__) do if exist "%%i" rd /s /q "%%i"
  for /r %%i in (*.pyc) do del /q "%%i"
  echo ✅ Limpieza completa
  goto :eof

:backup
  if not exist backups mkdir backups
  set TS=%DATE:~-4%-%DATE:~3,2%-%DATE:~0,2%_%TIME:~0,2%-%TIME:~3,2%-%TIME:~6,2%
  set TS=%TS: =0%
  if exist backend\inventario_evidencias.db copy /y backend\inventario_evidencias.db backups\inventario_evidencias_!TS!.db >nul
  echo ✅ Backup creado en carpeta backups
  goto :eof

:test
  echo 🔎 Verificando entorno...
  python --version
  uvicorn --version
  echo ✅ Pruebas basicas completadas
  goto :eof

:help
  echo Comandos disponibles:
  echo   manage.cmd setup   - Configurar proyecto
  echo   manage.cmd dev     - Servidor desarrollo
  echo   manage.cmd run     - Servidor produccion
  echo   manage.cmd status  - Estado del proyecto
  echo   manage.cmd clean   - Limpiar temporales
  echo   manage.cmd backup  - Backup BD
  echo   manage.cmd test    - Verificar entorno
  exit /b 0
