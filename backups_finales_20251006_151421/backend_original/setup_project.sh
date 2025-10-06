#!/bin/bash

# ------------------------------------------------------
# Script de configuración del proyecto Inventario
# ------------------------------------------------------

echo "1️⃣ Verificando entorno virtual..."
if [ ! -d "backend/.venv" ]; then
    echo "No se encontró .venv en backend, creando..."
    python -m venv backend/.venv
else
    echo ".venv ya existe, no se crea uno nuevo"
fi

echo "2️⃣ Activando entorno virtual..."
# Para Git Bash / WSL
source backend/.venv/bin/activate

echo "3️⃣ Instalando dependencias..."
pip install --upgrade pip
pip install -r backend/requirements.txt

echo "4️⃣ Creando carpeta static si no existe..."
mkdir -p backend/static

echo "5️⃣ Moviendo admin.html a static..."
if [ -f "backend/admin.html" ]; then
    mv backend/admin.html backend/static/admin.html
    echo "admin.html movido a backend/static/"
else
    echo "admin.html ya está en backend/static/ o no existe"
fi

echo "6️⃣ Ajustando app.py para servir archivos estáticos..."
APP_FILE="backend/app.py"

if ! grep -q "StaticFiles" "$APP_FILE"; then
    echo -e "\nfrom fastapi.staticfiles import StaticFiles\napp.mount('/static', StaticFiles(directory='static'), name='static')" >> "$APP_FILE"
    echo "Configuración de archivos estáticos añadida a app.py"
else
    echo "app.py ya tiene StaticFiles configurado"
fi

echo "7️⃣ Proyecto configurado correctamente."
echo "Ahora puedes ejecutar:"
echo "   cd backend"
echo "   source .venv/bin/activate  # o Activate.ps1 en Windows"
echo "   uvicorn app:app --reload --host 0.0.0.0 --port 8000"
