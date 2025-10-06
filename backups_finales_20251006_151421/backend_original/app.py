from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional, List
from datetime import datetime
import os, re, gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

app = FastAPI(title="Sistema Inventario SENA", version="2.1.0")
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

def get_google_sheet_data():
    try:
        # Cargar variables de entorno
        if os.path.exists("../.env"):
            load_dotenv("../.env")
        elif os.path.exists(".env"):
            load_dotenv(".env")

        sheet_id = os.getenv("GOOGLE_SHEET_ID", "1tCILvM3VkaACJMNnTZu4ZYM3x81HcoTlg6uoj-K6RRQ")
        creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
        if not os.path.exists(creds_path):
            return [{"id":"ERROR","placa":"ERROR","nombre":"Credenciales faltantes"}]

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly"
        ]
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_id)

        articles = []
        for ws in sheet.worksheets():
            rows = ws.get_all_values()
            if len(rows) <= 1:
                continue
            headers = rows[0]
            for row in rows[1:]:
                while len(row) < len(headers):
                    row.append("")
                d = dict(zip(headers, row))
                placa = d.get("Placa","").strip()
                if not placa:
                    continue
                nombre = d.get("Descripción Actual","").strip()
                marca = d.get("Marca","").strip()
                modelo = d.get("Modelo","").strip()
                if marca:
                    nombre += f" {marca}"
                if modelo:
                    nombre += f" {modelo}"
                valor = re.sub(r"[^0-9.]", "", d.get("Valor Ingreso","0"))
                try:
                    valor = float(valor)
                except:
                    valor = 0.0
                responsable = d.get("Responsable","Sin asignar").strip()
                articles.append({
                    "id": placa,
                    "placa": placa,
                    "nombre": nombre or "Artículo",
                    "categoria": d.get("Descripción Actual",""),
                    "valor": valor,
                    "responsable": responsable,
                    "hoja": ws.title
                })
        return articles or [{"id":"EMPTY","placa":"EMPTY","nombre":"Sin datos"}]
    except Exception as e:
        return [{"id":"ERROR","placa":"ERROR","nombre":f"Error: {e}"}]

_cache = None

@app.get("/")
async def root():
    try:
        return FileResponse("../frontend/admin.html")
    except:
        return {"message":"Sistema operativo","timestamp":datetime.utcnow().isoformat()}

@app.get("/api/articulos")
async def api_articulos():
    global _cache
    if _cache is None:
        _cache = get_google_sheet_data()
    return {"articulos": _cache, "total": len(_cache)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)

# ===== Endpoints AGREGADOS: Inventario =====

@app.get("/api/inventario/consulta")
async def consulta_inventario(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500)
):
    """Consulta paginada del inventario"""
    articulos = get_google_sheet_data()
    total = len(articulos)
    start = (page - 1) * limit
    return {
        "articulos": articulos[start:start+limit],
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit
    }

@app.get("/api/inventario/categorias")
async def get_categorias():
    """Obtener categorías únicas"""
    articulos = get_google_sheet_data()
    categorias = sorted({art.get("categoria","") for art in articulos})
    return categorias

@app.get("/api/inventario/responsables")
async def get_responsables():
    """Obtener responsables únicos"""
    articulos = get_google_sheet_data()
    responsables = sorted({art.get("responsable","") for art in articulos})
    return responsables

@app.get("/api/inventario/estadisticas")
async def get_estadisticas():
    """Estadísticas del inventario"""
    articulos = get_google_sheet_data()
    return {
        "total_articulos": len(articulos),
        "hojas_procesadas": len({art.get("hoja") for art in articulos})
    }
