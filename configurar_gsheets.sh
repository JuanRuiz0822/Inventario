#!/bin/bash

echo "----------- Ajuste de implementación Google Sheets y backend FastAPI -----------"

# Variables de entorno (edita el ID si aplicable)
SHEET_ID_DEFAULT="1tCILvM3VkaACJMNnTZu4ZYM3x81HcoTlg6uoj-K6RRQ"

# 1. Crear archivo .env si no existe
if [ ! -f .env ]; then
    echo "GOOGLE_SHEET_ID=$SHEET_ID_DEFAULT" > .env
    echo "GOOGLE_CREDENTIALS_PATH=credentials.json" >> .env
    echo ".env creado, revisa que el ID sea el correcto."
else
    echo ".env ya existe. Valida que el GOOGLE_SHEET_ID y CREDENTIALS sean correctos."
fi

# 2. Verificar archivo de credenciales
if [ ! -f credentials.json ]; then
    echo "ATENCIÓN: credentials.json no se encuentra en este directorio."
    echo "Descarga desde Google Cloud Console y colócalo aquí."
else
    echo "Archivo credentials.json detectado."
fi

echo ""
echo "3. Recuerda compartir tu hoja de Google Sheets con la cuenta:"
if [ -f credentials.json ]; then
    python3 -c "import json; print(json.load(open('credentials.json'))['client_email'])"
else
    echo "Sin credenciales.json, no se puede extraer cuenta. Hazlo manualmente."
fi
echo ""
echo "4. Si cambiaste algo, reinicia el backend:"
echo "   python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "----------- Fin del script -----------"
