@echo off
setlocal

if "%1"=="setup" goto setup
if "%1"=="dev" goto dev
if "%1"=="run" goto run
if "%1"=="clean" goto clean
if "%1"=="status" goto status
if "%1"=="backup" goto backup
if "%1"=="test" goto test
goto help

:setup
echo 🔧 Configurando proyecto...
if not exist .venv (
    python -m venv .venv
    echo ✅ Entorno virtual creado
)
call .venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt --upgrade
mkdir data\uploads 2>nul
mkdir data\backups 2>nul
mkdir logs 2>nul
echo.
echo ✅ Proyecto configurado completamente
echo.
echo 📖 Próximo paso: manage.cmd dev
goto end

:dev
echo 🚀 Iniciando servidor de desarrollo...
call .venv\Scripts\activate.bat
cd backend
echo.
echo 🌐 Sistema disponible en:
echo   - API Docs: http://localhost:8000/docs
echo   - Admin Panel: http://localhost:8000/admin.html  
echo   - ReDoc: http://localhost:8000/redoc
echo.
echo 💡 Presiona Ctrl+C para detener el servidor
echo.
uvicorn app:app --reload --host 127.0.0.1 --port 8000 --log-level info
goto end

:run
echo 🚀 Iniciando servidor de producción...
call .venv\Scripts\activate.bat
cd backend
uvicorn app:app --host 0.0.0.0 --port 8000
goto end

:clean
echo 🧹 Limpiando archivos temporales...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
del /s /q *.pyc 2>nul
del /s /q *.log 2>nul
echo ✅ Archivos temporales eliminados
goto end

:status
echo 📊 Estado del proyecto:
echo.
echo 🏗️  Estructura del proyecto:
if exist .venv echo   ✅ Entorno virtual: Activo
if not exist .venv echo   ❌ Entorno virtual: No existe
if exist backend\inventario.db echo   ✅ Base de datos: Existe
if not exist backend\inventario.db echo   ⚠️  Base de datos: Se creará al iniciar
if exist config echo   ✅ Configuración: Existe
if exist data echo   ✅ Directorio datos: Existe  
if exist manage.cmd echo   ✅ Scripts gestión: Disponibles
echo.
echo 📦 Para ver dependencias instaladas: manage.cmd test
goto end

:backup
echo 💾 Creando backup de base de datos...
if not exist data\backups mkdir data\backups
set backup_name=backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set backup_name=%backup_name: =0%
if exist backend\inventario.db (
    copy backend\inventario.db data\backups\%backup_name%.db >nul 2>&1
    echo ✅ Backup creado exitosamente: data\backups\%backup_name%.db
) else (
    echo ⚠️  Base de datos no encontrada en backend\inventario.db
    echo    La base de datos se crea automáticamente al iniciar el servidor
)
goto end

:test
echo 🧪 Ejecutando verificaciones del sistema...
call .venv\Scripts\activate.bat
echo.
echo 📋 Verificando dependencias principales...
python -c "
import sys
print(f'Python: {sys.version}')
try:
    import fastapi
    print(f'✅ FastAPI: {fastapi.__version__}')
except ImportError:
    print('❌ FastAPI: No instalado')

try:
    import uvicorn
    print(f'✅ Uvicorn: {uvicorn.__version__}')
except ImportError:
    print('❌ Uvicorn: No instalado')

try:
    import pandas
    print(f'✅ Pandas: {pandas.__version__}')
except ImportError:
    print('❌ Pandas: No instalado')

try:
    import gspread
    print('✅ GSpread: Instalado')
except ImportError:
    print('❌ GSpread: No instalado')

print('\n📂 Verificando estructura:')
import pathlib
if pathlib.Path('backend/app.py').exists():
    print('✅ Backend app.py: Existe')
else:
    print('❌ Backend app.py: No encontrado')

if pathlib.Path('config/settings.py').exists():
    print('✅ Configuración: Existe')
else:
    print('❌ Configuración: No encontrada')

print('\n✅ Verificación completada')
"
goto end

:help
echo.
echo ================================================
echo   Sistema de Inventario - Windows v3.0 Final
echo ================================================
echo.
echo 📋 Comandos disponibles:
echo   setup    - Configurar proyecto inicial
echo   dev      - Iniciar en modo desarrollo ⭐
echo   run      - Iniciar en modo producción
echo   clean    - Limpiar archivos temporales
echo   status   - Ver estado completo del proyecto
echo   backup   - Crear backup de base de datos
echo   test     - Verificar sistema y dependencias
echo   help     - Mostrar esta ayuda
echo.
echo 📖 Ejemplos de uso:
echo   manage.cmd setup     # Primera configuración
echo   manage.cmd dev       # Uso diario de desarrollo
echo   manage.cmd status    # Ver estado del proyecto
echo.
echo 🌐 URLs después de iniciar con 'dev':
echo   http://localhost:8000/docs      - Documentación interactiva
echo   http://localhost:8000/admin.html - Panel de administración
echo.
echo 💡 Optimizado para Windows con Python 3.13.5
echo.

:end
