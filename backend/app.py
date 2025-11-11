
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

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sistema Inventario SENA",
    version="3.0.0",
    description="Sistema de gestión de inventario con Google Sheets"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos
try:
    app.mount("/static", StaticFiles(directory="../frontend"), name="static")
    logger.info("Archivos estáticos montados correctamente")
except Exception as e:
    logger.warning(f"No se pudieron montar archivos estáticos: {e}")

# Cache global
_cache = None
_cache_timestamp = None

def normaliza_texto(texto):
    """Normaliza texto para comparaciones"""
    if not texto:
        return ""
    return str(texto).strip().upper()

def normaliza_placa(placa):
    """Normaliza placas eliminando espacios, guiones y ceros iniciales"""
    if not placa:
        return ""
    placa_norm = str(placa).replace(" ", "").replace("-", "").replace("_", "")
    placa_norm = placa_norm.strip().lstrip("0").upper()
    return placa_norm if placa_norm else "0"

def detectar_columna(headers, palabras_clave):
    """Detecta índice de columna basándose en palabras clave"""
    headers_lower = [h.lower().strip() for h in headers]
    for idx, header in enumerate(headers_lower):
        for palabra in palabras_clave:
            if palabra.lower() in header:
                return idx
    return None

def get_google_sheet_data():
    """
    Obtiene datos de Google Sheets con mapeo inteligente de columnas
    y validación robusta de datos
    """
    try:
        # Cargar variables de entorno
        load_dotenv()
        sheet_id = os.getenv("GOOGLE_SHEET_ID")
        creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
        
        if not sheet_id:
            logger.error("GOOGLE_SHEET_ID no configurado en .env")
            return [{"id":"ERROR","placa":"ERROR","nombre":"GOOGLE_SHEET_ID no configurado"}]
        
        if not os.path.exists(creds_path):
            logger.error(f"Archivo de credenciales no encontrado: {creds_path}")
            return [{"id":"ERROR","placa":"ERROR","nombre":"Credenciales no encontradas"}]
        
        # Conectar a Google Sheets
        logger.info("Conectando a Google Sheets...")
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly"
        ]
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_id)
        
        logger.info(f"Conectado exitosamente a: {sheet.title}")
        
        articles = []
        total_sheets = 0
        total_rows_processed = 0
        
        # Procesar cada hoja
        for ws in sheet.worksheets():
            total_sheets += 1
            sheet_name = ws.title
            
            try:
                rows = ws.get_all_values()
                
                if len(rows) <= 1:
                    logger.warning(f"Hoja '{sheet_name}' vacía o solo con encabezados")
                    continue
                
                headers = rows[0]
                logger.info(f"Procesando hoja: '{sheet_name}' ({len(rows)-1} filas)")
                
                # Mapeo inteligente de columnas
                col_map = {
                    'placa': detectar_columna(headers, ['placa', 'código', 'codigo', 'id', 'identificador']),
                    'descripcion': detectar_columna(headers, ['descripción', 'descripcion', 'descripcion actual', 'artículo', 'articulo', 'nombre']),
                    'marca': detectar_columna(headers, ['marca', 'fabricante']),
                    'modelo': detectar_columna(headers, ['modelo', 'model']),
                    'valor': detectar_columna(headers, ['valor', 'precio', 'valor ingreso', 'costo']),
                    'fecha': detectar_columna(headers, ['fecha', 'fecha adquisición', 'fecha adquisicion', 'fecha compra']),
                    'ubicacion': detectar_columna(headers, ['ubicación', 'ubicacion', 'lugar', 'sitio']),
                    'responsable': detectar_columna(headers, ['responsable', 'responsable actual', 'origen', 'custodio', 'encargado'])
                }
                
                # Log del mapeo
                mapeo_log = {k: headers[v] if v is not None else 'N/A' for k, v in col_map.items()}
                logger.info(f"Mapeo de columnas para '{sheet_name}': {mapeo_log}")
                
                # Procesar cada fila
                for row_idx, row in enumerate(rows[1:], start=2):
                    # Asegurar que la fila tenga suficientes columnas
                    while len(row) < len(headers):
                        row.append("")
                    
                    # Extraer placa (campo obligatorio)
                    placa_idx = col_map.get('placa')
                    if placa_idx is None or placa_idx >= len(row):
                        continue
                    
                    placa = row[placa_idx].strip()
                    if not placa or placa == "":
                        continue
                    
                    # Extraer otros campos con valores por defecto
                    descripcion = row[col_map['descripcion']].strip() if col_map.get('descripcion') is not None and col_map['descripcion'] < len(row) else ""
                    marca = row[col_map['marca']].strip() if col_map.get('marca') is not None and col_map['marca'] < len(row) else ""
                    modelo = row[col_map['modelo']].strip() if col_map.get('modelo') is not None and col_map['modelo'] < len(row) else ""
                    
                    # Construir nombre completo inteligente
                    nombre_parts = []
                    if descripcion and descripcion.upper() not in ["NA", "N/A", "N.A.", ""]:
                        nombre_parts.append(descripcion)
                    if marca and marca.upper() not in ["NA", "N/A", "N.A.", "", "SIN MARCA"]:
                        nombre_parts.append(marca)
                    if modelo and modelo.upper() not in ["NA", "N/A", "N.A.", "", "SIN MODELO"]:
                        nombre_parts.append(modelo)
                    
                    nombre = " ".join(nombre_parts) if nombre_parts else f"Artículo {placa}"
                    
                    # Procesar valor numérico
                    valor = 0.0
                    if col_map.get('valor') is not None and col_map['valor'] < len(row):
                        valor_str = re.sub(r"[^0-9.]", "", row[col_map['valor']])
                        try:
                            valor = float(valor_str) if valor_str else 0.0
                        except:
                            valor = 0.0
                    
                    # Fecha
                    fecha = ""
                    if col_map.get('fecha') is not None and col_map['fecha'] < len(row):
                        fecha = row[col_map['fecha']].strip()
                    
                    # Ubicación
                    ubicacion = "SENA"
                    if col_map.get('ubicacion') is not None and col_map['ubicacion'] < len(row):
                        ubicacion_raw = row[col_map['ubicacion']].strip()
                        if ubicacion_raw and ubicacion_raw.upper() not in ["NA", "N/A", "N.A.", ""]:
                            ubicacion = ubicacion_raw
                    
                    # Responsable
                    responsable = sheet_name
                    if col_map.get('responsable') is not None and col_map['responsable'] < len(row):
                        responsable_raw = row[col_map['responsable']].strip()
                        if responsable_raw and responsable_raw.upper() not in ["NA", "N/A", "N.A.", ""]:
                            responsable = responsable_raw
                    
                    # Crear registro de artículo
                    articulo = {
                        "id": placa,
                        "placa": placa,
                        "placa_normalizada": normaliza_placa(placa),
                        "nombre": nombre,
                        "descripcion": descripcion,
                        "modelo": modelo,
                        "marca": marca,
                        "categoria": descripcion or "Sin categoría",
                        "valor": valor,
                        "fecha_adquisicion": fecha,
                        "ubicacion": ubicacion,
                        "responsable": responsable,
                        "hoja": sheet_name,
                        "fila": row_idx
                    }
                    
                    articles.append(articulo)
                    total_rows_processed += 1
                    
            except Exception as e:
                logger.error(f"Error procesando hoja '{sheet_name}': {e}")
                continue
        
        logger.info(f"✓ Procesamiento completado: {total_rows_processed} artículos de {total_sheets} hojas")
        
        if not articles:
            return [{"id": "EMPTY", "placa": "EMPTY", "nombre": "No se encontraron artículos"}]
        
        return articles
        
    except gspread.exceptions.SpreadsheetNotFound:
        logger.error("Google Sheet no encontrado. Verifica el ID y los permisos.")
        return [{"id":"ERROR","placa":"ERROR","nombre":"Hoja no encontrada o sin permisos"}]
    except Exception as e:
        logger.error(f"Error general: {type(e).__name__}: {e}")
        return [{"id": "ERROR", "placa": "ERROR", "nombre": f"Error: {str(e)}"}]

@app.on_event("startup")
async def startup_event():
    """Evento de inicio: cargar cache inicial"""
    global _cache, _cache_timestamp
    logger.info("Iniciando aplicación...")
    _cache = get_google_sheet_data()
    _cache_timestamp = datetime.now()
    logger.info(f"Cache inicial cargado: {len(_cache)} artículos")

@app.get("/")
async def root():
    """Ruta raíz - retorna el frontend"""
    try:
        return FileResponse("../frontend/admin.html")
    except:
        return {
            "message": "Sistema Inventario SENA v3.0",
            "status": "online",
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/health")
async def health_check():
    """Health check del sistema"""
    global _cache, _cache_timestamp
    return {
        "status": "healthy",
        "version": "3.0.0",
        "cache_size": len(_cache) if _cache else 0,
        "cache_timestamp": _cache_timestamp.isoformat() if _cache_timestamp else None,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/articulos")
async def api_articulos():
    """Obtener todos los artículos (con cache)"""
    global _cache
    if _cache is None:
        _cache = get_google_sheet_data()
    return {"articulos": _cache, "total": len(_cache)}

@app.get("/api/inventario/consulta")
async def consulta_inventario(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500)
):
    """Consulta paginada del inventario"""
    articulos = get_google_sheet_data()
    total = len(articulos)
    start = (page - 1) * limit
    end = start + limit
    
    return {
        "articulos": articulos[start:end],
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit
    }

@app.get("/api/inventario/categorias")
async def get_categorias():
    """Obtener lista de categorías únicas"""
    articulos = get_google_sheet_data()
    categorias = sorted(set(
        art.get("categoria", "") 
        for art in articulos 
        if art.get("categoria") and art.get("categoria") not in ["", "ERROR", "EMPTY"]
    ))
    return categorias

@app.get("/api/inventario/responsables")
async def get_responsables():
    """Obtener lista de responsables únicos"""
    articulos = get_google_sheet_data()
    responsables = sorted(set(
        art.get("responsable", "") 
        for art in articulos 
        if art.get("responsable") and art.get("responsable") not in ["", "ERROR", "EMPTY"]
    ))
    return responsables

@app.get("/api/inventario/estadisticas")
async def get_estadisticas():
    """Obtener estadísticas del inventario"""
    articulos = get_google_sheet_data()
    
    # Filtrar artículos válidos
    articulos_validos = [a for a in articulos if a.get("placa") not in ["ERROR", "EMPTY"]]
    
    return {
        "total_articulos": len(articulos_validos),
        "hojas_procesadas": len(set(art.get("hoja", "") for art in articulos_validos)),
        "valor_total": sum(art.get("valor", 0) for art in articulos_validos),
        "categorias_unicas": len(set(art.get("categoria", "") for art in articulos_validos if art.get("categoria"))),
        "responsables_unicos": len(set(art.get("responsable", "") for art in articulos_validos if art.get("responsable")))
    }

@app.get('/api/cuentadantes')
async def cuentadantes():
    """Obtener lista de cuentadantes"""
    data = get_google_sheet_data()
    responsables = set()
    
    for art in data:
        r = art.get('responsable', '').strip()
        if r and r not in ["", "ERROR", "EMPTY", "NA", "N/A", "N.A."]:
            responsables.add(r)
    
    return {'cuentadantes': sorted(responsables)}

@app.get('/api/cuentadantes/{nombre}/articulos')
async def articulos_por_cuentadante(nombre: str):
    """Obtener artículos de un cuentadante específico"""
    data = get_google_sheet_data()
    nombre_norm = normaliza_texto(nombre)
    
    articulos = [
        art for art in data 
        if normaliza_texto(art.get('responsable', '')) == nombre_norm
    ]
    
    if not articulos:
        raise HTTPException(404, f"No se encontraron artículos para el cuentadante: {nombre}")
    
    return {
        'cuentadante': nombre,
        'articulos': articulos,
        'total': len(articulos),
        'valor_total': sum(art.get('valor', 0) for art in articulos)
    }

@app.get("/api/inventario/{placa}/detalle")
async def detalle_articulo(placa: str):
    """Obtener detalle de un artículo por placa"""
    articulos = get_google_sheet_data()
    placa_norm = normaliza_placa(placa)
    
    logger.info(f"Buscando detalle para placa: '{placa}' (normalizada: '{placa_norm}')")
    
    # Buscar por placa normalizada
    for art in articulos:
        art_placa_norm = normaliza_placa(art.get('placa', ''))
        if art_placa_norm == placa_norm:
            logger.info(f"✓ Detalle encontrado: {art.get('nombre')}")
            return {"articulo": art}
    
    # Si no se encuentra, buscar por placa original
    for art in articulos:
        if art.get('placa', '').strip() == placa.strip():
            logger.info(f"✓ Detalle encontrado (búsqueda original): {art.get('nombre')}")
            return {"articulo": art}
    
    logger.warning(f"✗ Placa no encontrada: '{placa}'")
    raise HTTPException(404, f"Artículo con placa '{placa}' no encontrado")

@app.post("/api/inventario/refresh")
async def refresh_cache():
    """Refrescar cache manualmente"""
    global _cache, _cache_timestamp
    logger.info("Refrescando cache manualmente...")
    _cache = get_google_sheet_data()
    _cache_timestamp = datetime.now()
    return {
        "message": "Cache actualizado exitosamente",
        "total_articulos": len(_cache),
        "timestamp": _cache_timestamp.isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
