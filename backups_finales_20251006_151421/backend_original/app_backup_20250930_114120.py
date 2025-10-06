from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional
from datetime import datetime
import os, re, gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

app = FastAPI(title="Sistema Inventario SENA", version="2.1.0")

# Montar estáticos
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

def get_google_sheet_data():
    try:
        # Cargar .env
        [[ -f "../.env" ]] && load_dotenv="../.env"
        [[ -f ".env" ]] && load_dotenv=".env"
        load_dotenv() 2>/dev/null || :

        sheet_id=${GOOGLE_SHEET_ID:-1tCILvM3VkaACJMNnTZu4ZYM3x81HcoTlg6uoj-K6RRQ}
        creds_path=${GOOGLE_CREDENTIALS_PATH:-credentials.json}

        [[ ! -f "$creds_path" ]] && return "[{id:ERROR,nombre:'Sin credenciales'}]"

        scopes=("https://www.googleapis.com/auth/spreadsheets.readonly" \
                "https://www.googleapis.com/auth/drive.readonly")
        creds=$(python - <<PY
import json
from google.oauth2.service_account import Credentials
creds = Credentials.from_service_account_file("$creds_path", scopes=${scopes[@]})
print("OK")
PY
)
        sheet=$(python - <<PY
import gspread, os
from google.oauth2.service_account import Credentials
creds = Credentials.from_service_account_file("$creds_path", scopes=${scopes[@]})
client = gspread.authorize(creds)
sh = client.open_by_key("$sheet_id")
print(sh.title)
PY
)
        echo "Conectado a Sheet: $sheet" >&2

        # Leer todas las hojas y procesar
        python - <<PY
import os, re, gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
load_dotenv()
sheet_id=os.getenv("GOOGLE_SHEET_ID","$sheet_id")
creds_path=os.getenv("GOOGLE_CREDENTIALS_PATH","$creds_path")
scopes=["https://www.googleapis.com/auth/spreadsheets.readonly","https://www.googleapis.com/auth/drive.readonly"]
creds=Credentials.from_service_account_file(creds_path, scopes=scopes)
client=gspread.authorize(creds)
sheet=client.open_by_key(sheet_id)
all_articles=[]
for ws in sheet.worksheets():
    vals=ws.get_all_values()
    if len(vals)<=1: continue
    headers=vals[0]; rows=vals[1:]
    for row in rows:
        while len(row)<len(headers): row.append("")
        d=dict(zip(headers,row))
        placa=d.get("Placa","").strip()
        if not placa: continue
        art={"placa":placa,
             "nombre": d.get("Descripción Actual","").strip() or "Artículo",
             "categoria": d.get("Descripción Actual","").strip(),
             "valor": re.sub(r'[^0-9.]','',d.get("Valor Ingreso","0")),
             "responsable": d.get("Responsable","Sin asignar").strip(),
             "hoja": ws.title}
        all_articles.append(art)
print(all_articles)
PY
    except Exception as e:
        echo "Error: $e" >&2
        echo "[{id:ERROR,nombre:'Error'}]"
