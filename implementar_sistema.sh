#!/bin/bash

echo "============================================================"
echo "   IMPLEMENTACIÓN CORRECTA - Sistema Inventario SENA"
echo "============================================================"
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Paso 1: Verificar estructura del proyecto
echo -e "${YELLOW}[1/6] Verificando estructura del proyecto...${NC}"
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}ERROR: Faltan carpetas 'backend' o 'frontend'${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Estructura correcta${NC}"

# Paso 2: Crear/actualizar archivo .env
echo -e "${YELLOW}[2/6] Configurando variables de entorno...${NC}"
cat > backend/.env << 'EOF'
GOOGLE_SHEET_ID=1tCILvM3VkaACJMNnTZu4ZYM3x81HcoTlg6uoj-K6RRQ
GOOGLE_CREDENTIALS_PATH=credentials.json
EOF
echo -e "${GREEN}✓ Archivo .env creado${NC}"

# Paso 3: Verificar credenciales
echo -e "${YELLOW}[3/6] Verificando credenciales de Google...${NC}"
if [ ! -f "backend/credentials.json" ]; then
    echo -e "${RED}⚠ IMPORTANTE: credentials.json no encontrado${NC}"
    echo "Debes colocar tu archivo credentials.json en la carpeta 'backend'"
    echo "Descárgalo desde: https://console.cloud.google.com"
else
    echo -e "${GREEN}✓ Credenciales encontradas${NC}"
    # Extraer email de la cuenta de servicio
    SERVICE_EMAIL=$(python3 -c "import json; print(json.load(open('backend/credentials.json'))['client_email'])" 2>/dev/null || echo "No se pudo leer")
    echo -e "${YELLOW}Cuenta de servicio: ${SERVICE_EMAIL}${NC}"
    echo -e "${YELLOW}IMPORTANTE: Comparte tu Google Sheet con este email${NC}"
fi

# Paso 4: Actualizar app.py con la implementación correcta
echo -e "${YELLOW}[4/6] Actualizando backend (app.py)...${NC}"

cat > backend/app.py << 'PYTHONCODE'
from fastapi import FastAPI, Query, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
import re
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Sistema Inventario SENA", version="3.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

def get_google_sheet_data():
    """Obtiene datos de Google Sheets con mapeo robusto de columnas"""
    try:
        # Cargar variables de entorno
        load_dotenv()
        sheet_id = os.getenv("GOOGLE_SHEET_ID")
        creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
        
        if not os.path.exists(creds_path):
            logger.error(f"Archivo de credenciales no encontrado: {creds_path}")
            return [{"id":"ERROR","placa":"ERROR","nombre":"Credenciales no encontradas"}]
        
        # Conectar a Google Sheets
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly"
        ]
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_id)
        
        articles = []
        total_sheets = 0
        
        for ws in sheet.worksheets():
            total_sheets += 1
            try:
                rows = ws.get_all_values()
                if len(rows) <= 1:
                    continue
                
                headers = [h.strip().lower() for h in rows[0]]
                logger.info(f"Procesando hoja: {ws.title} con {len(rows)-1} filas")
                
                # Mapeo flexible de columnas
                col_map = {}
                for idx, header in enumerate(headers):
                    if 'placa' in header:
                        col_map['placa'] = idx
                    elif 'descripci' in header or 'descripcion' in header:
                        col_map['descripcion'] = idx
                    elif 'marca' in header:
                        col_map['marca'] = idx
                    elif 'modelo' in header:
                        col_map['modelo'] = idx
                    elif 'valor' in header and 'ingreso' in header:
                        col_map['valor'] = idx
                    elif 'fecha' in header and ('adquis' in header or 'compra' in header):
                        col_map['fecha'] = idx
                    elif 'ubicaci' in header:
                        col_map['ubicacion'] = idx
                    elif 'responsable' in header or 'origen' in header:
                        col_map['responsable'] = idx
                
                # Procesar filas
                for row_idx, row in enumerate(rows[1:], start=2):
                    while len(row) < len(headers):
                        row.append("")
                    
                    placa = row[col_map.get('placa', 0)].strip() if col_map.get('placa') is not None else ""
                    if not placa or placa == "":
                        continue
                    
                    descripcion = row[col_map.get('descripcion', 1)].strip() if col_map.get('descripcion') is not None else ""
                    marca = row[col_map.get('marca', 2)].strip() if col_map.get('marca') is not None else ""
                    modelo = row[col_map.get('modelo', 3)].strip() if col_map.get('modelo') is not None else ""
                    
                    # Construir nombre completo
                    nombre_parts = [descripcion, marca, modelo]
                    nombre = " ".join([p for p in nombre_parts if p and p.upper() != "NA"])
                    
                    # Valor
                    valor_str = ""
                    if col_map.get('valor') is not None:
                        valor_str = re.sub(r"[^0-9.]", "", row[col_map['valor']])
                    try:
                        valor = float(valor_str) if valor_str else 0.0
                    except:
                        valor = 0.0
                    
                    # Fecha
                    fecha = row[col_map.get('fecha', -1)].strip() if col_map.get('fecha') is not None else ""
                    
                    # Ubicación
                    ubicacion = row[col_map.get('ubicacion', -1)].strip() if col_map.get('ubicacion') is not None else "SENA"
                    
                    # Responsable
                    responsable = row[col_map.get('responsable', -1)].strip() if col_map.get('responsable') is not None else ws.title
                    
                    articulo = {
                        "id": placa,
                        "placa": placa,
                        "nombre": nombre or "Artículo sin descripción",
                        "modelo": modelo,
                        "marca": marca,
                        "categoria": descripcion or "Sin categoría",
                        "valor": valor,
                        "fecha_adquisicion": fecha,
                        "ubicacion": ubicacion,
                        "responsable": responsable,
                        "hoja": ws.title
                    }
                    articles.append(articulo)
                    
            except Exception as e:
                logger.error(f"Error procesando hoja {ws.title}: {e}")
                continue
        
        logger.info(f"Total de artículos procesados: {len(articles)} de {total_sheets} hojas")
        return articles if articles else [{"id": "EMPTY", "placa": "EMPTY", "nombre": "Sin datos"}]
        
    except Exception as e:
        logger.error(f"Error general en get_google_sheet_data: {e}")
        return [{"id": "ERROR", "placa": "ERROR", "nombre": f"Error: {str(e)}"}]

_cache = None

@app.get("/")
async def root():
    try:
        return FileResponse("../frontend/admin.html")
    except:
        return {"message": "Sistema Inventario SENA v3.0", "status": "online"}

@app.get("/api/articulos")
async def api_articulos():
    global _cache
    if _cache is None:
        _cache = get_google_sheet_data()
    return {"articulos": _cache, "total": len(_cache)}

@app.get("/api/inventario/consulta")
async def consulta_inventario(page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=500)):
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
    articulos = get_google_sheet_data()
    categorias = sorted({art.get("categoria", "") for art in articulos if art.get("categoria")})
    return categorias

@app.get("/api/inventario/responsables")
async def get_responsables():
    articulos = get_google_sheet_data()
    responsables = sorted({art.get("responsable", "") for art in articulos if art.get("responsable")})
    return responsables

@app.get("/api/inventario/estadisticas")
async def get_estadisticas():
    articulos = get_google_sheet_data()
    return {
        "total_articulos": len(articulos),
        "hojas_procesadas": len({art.get("hoja") for art in articulos}),
        "valor_total": sum(art.get("valor", 0) for art in articulos)
    }

@app.get('/api/cuentadantes')
async def cuentadantes():
    data = get_google_sheet_data()
    responsables = set()
    for art in data:
        r = art.get('responsable', '')
        if r and r not in ["", "ERROR", "EMPTY"]:
            responsables.add(r)
    return {'cuentadantes': sorted(responsables)}

@app.get('/api/cuentadantes/{nombre}/articulos')
async def articulos_por_cuentadante(nombre: str):
    data = get_google_sheet_data()
    articulos = [
        art for art in data if art.get('responsable', '').strip().lower() == nombre.strip().lower()
    ]
    if not articulos:
        raise HTTPException(404, "No se encontraron articulos para ese cuentadante.")
    return {'cuentadante': nombre, 'articulos': articulos, 'total': len(articulos)}

def normaliza_placa(p):
    return str(p).replace(" ", "").replace("-", "").strip().upper()

@app.get("/api/inventario/{placa}/detalle")
async def detalle_articulo(placa: str):
    articulos = get_google_sheet_data()
    placa_norm = normaliza_placa(placa)
    
    for art in articulos:
        if normaliza_placa(art.get('placa', '')) == placa_norm:
            logger.info(f"Detalle encontrado para placa: {placa}")
            return {"articulo": art}
    
    logger.warning(f"Placa no encontrada: {placa}")
    raise HTTPException(404, "Artículo no encontrado")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
PYTHONCODE

echo -e "${GREEN}✓ Backend actualizado${NC}"

# Paso 5: Instalar dependencias
echo -e "${YELLOW}[5/6] Instalando dependencias Python...${NC}"
cd backend
if [ -d ".venv" ]; then
    source .venv/Scripts/activate 2>/dev/null || source .venv/bin/activate
fi
pip install -q fastapi uvicorn python-dotenv gspread google-auth openpyxl
echo -e "${GREEN}✓ Dependencias instaladas${NC}"
cd ..

# Paso 6: Instrucciones finales
echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}   ✓ IMPLEMENTACIÓN COMPLETADA${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo -e "${YELLOW}PASOS FINALES:${NC}"
echo ""
echo "1. Asegúrate de tener credentials.json en backend/"
echo ""
echo "2. Comparte tu Google Sheet con el email de la cuenta de servicio"
echo "   (mostrado arriba)"
echo ""
echo "3. Inicia el servidor:"
echo -e "   ${GREEN}cd backend${NC}"
echo -e "   ${GREEN}python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000${NC}"
echo ""
echo "4. Accede en el navegador:"
echo -e "   ${GREEN}http://localhost:8000/${NC}"
echo ""
echo -e "${YELLOW}Para verificar que la conexión funciona, revisa los logs del servidor.${NC}"
echo -e "${YELLOW}Deberías ver 'Total de artículos procesados: X'${NC}"
echo ""
