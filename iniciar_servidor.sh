#!/bin/bash
echo "Iniciando Sistema Inventario SENA..."
cd backend
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
