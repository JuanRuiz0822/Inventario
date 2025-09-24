#!/bin/bash

echo "1️⃣ Verificando entorno virtual..."
if [ ! -d ".venv" ]; then
    echo ".venv no existe, creando..."
    python -m venv .venv
else
    echo ".venv ya existe, no se crea uno nuevo"
fi

echo "2️⃣ Activando entorno virtual..."
# Activación en Windows (Git Bash)
source .venv/Scripts/activate || echo "Activa manualmente con .venv/Scripts/Activate.ps1"

echo "3️⃣ Instalando dependencias..."
if [ -f "requirements.txt" ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "No se encontró requirements.txt, verifica que esté en backend/"
fi

echo "4️⃣ Creando carpeta static si no existe..."
if [ ! -d "static" ]; then
    mkdir static
    echo "Carpeta static creada"
else
    echo "Carpeta static ya existe"
fi

echo "5️⃣ Verificando admin.html..."
if [ -f "static/admin.html" ]; then
    echo "admin.html ya está en static/"
elif [ -f "../admin.html" ]; then
    mv ../admin.html static/
    echo "admin.html movido a static/"
else
    echo "No se encontró admin.html"
fi

echo "✅ Setup completado. Para iniciar el proyecto:"
echo "cd backend"
echo "source .venv/Scripts/activate  # o Activate.ps1 en PowerShell"
echo "uvicorn app:app --reload --host 0.0.0.0 --port 8000"
