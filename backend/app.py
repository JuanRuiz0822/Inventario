from fastapi import FastAPI, Query, HTTPException, Body, UploadFile, File
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
import shutil
import sqlite3
from typing import List
from threading import Lock
import asyncio

# ========= CONFIGURACIÓN OPTIMIZADA - CACHE INTELIGENTE =========
CACHE_TTL = 3600  # 1 hora (ajustar según necesidad: 3600 = 1h, 7200 = 2h, etc.)
_cache = None
_cache_timestamp = None
_cache_lock = Lock()  # Thread-safe para peticiones concurrentes

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Sistema Inventario SENA",
    version="3.0.3-OPTIMIZADO-RAM",
    description="Sistema de gestión de inventario OPTIMIZADO con Cache Inteligente en RAM"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos del frontend
try:
    app.mount("/static", StaticFiles(directory="../frontend"), name="static")
    logger.info("✓ Archivos estáticos montados correctamente")
except Exception as e:
    logger.warning(f"⚠️ No se pudieron montar archivos estáticos: {e}")

# Carpeta local para evidencias e imágenes subidas
EVIDENCIAS_DIR = os.path.join("uploaded_evidencias")
os.makedirs(EVIDENCIAS_DIR, exist_ok=True)

# Servir evidencias como archivos estáticos
try:
    app.mount("/evidencias", StaticFiles(directory=EVIDENCIAS_DIR), name="evidencias")
    logger.info("✓ Carpeta de evidencias montada correctamente")
except Exception as e:
    logger.warning(f"⚠️ No se pudieron montar evidencias: {e}")

# ========= CONFIGURACIÓN BASE DE DATOS SQLite =========
DB_PATH = os.path.join(os.path.dirname(__file__), "inventario_evidencias.db")

def init_database():
    """Inicializa la base de datos SQLite con la tabla de evidencias"""
    try:
        db_dir = os.path.dirname(DB_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS evidencias_urls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                placa TEXT NOT NULL,
                url TEXT NOT NULL,
                filename TEXT NOT NULL,
                fecha_subida TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(placa, filename)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_placa 
            ON evidencias_urls(placa)
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"✅ Base de datos SQLite inicializada: {DB_PATH}")
        
        if os.path.exists(DB_PATH):
            logger.info(f"✓ Archivo DB creado correctamente (tamaño: {os.path.getsize(DB_PATH)} bytes)")
    except Exception as e:
        logger.error(f"❌ Error inicializando base de datos: {e}")
        raise

def guardar_url_evidencia(placa: str, url: str, filename: str):
    """Guarda la URL de una evidencia en la base de datos"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id FROM evidencias_urls 
            WHERE placa = ? AND filename = ?
        ''', (placa, filename))
        
        existe = cursor.fetchone()
        
        if existe:
            cursor.execute('''
                UPDATE evidencias_urls 
                SET url = ?, fecha_subida = CURRENT_TIMESTAMP
                WHERE placa = ? AND filename = ?
            ''', (url, placa, filename))
            logger.info(f"✓ URL actualizada en BD: {placa} -> {filename}")
        else:
            cursor.execute('''
                INSERT INTO evidencias_urls (placa, url, filename)
                VALUES (?, ?, ?)
            ''', (placa, url, filename))
            logger.info(f"✓ URL insertada en BD: {placa} -> {filename}")
        
        conn.commit()
        cursor.execute('''
            SELECT COUNT(*) FROM evidencias_urls 
            WHERE placa = ? AND filename = ?
        ''', (placa, filename))
        count = cursor.fetchone()[0]
        conn.close()
        
        if count > 0:
            logger.info(f"✅ Verificación exitosa: URL guardada para {placa}")
            return True
        else:
            logger.error(f"❌ Verificación falló: URL NO se guardó para {placa}")
            return False
            
    except sqlite3.IntegrityError as e:
        logger.error(f"❌ Error de integridad en BD: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Error guardando URL en BD: {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def obtener_urls_evidencias(placa: str) -> List[dict]:
    """Obtiene todas las URLs de evidencias de una placa"""
    try:
        if not os.path.exists(DB_PATH):
            logger.warning(f"⚠️ Base de datos no existe: {DB_PATH}")
            return []
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT url, filename, fecha_subida
            FROM evidencias_urls
            WHERE placa = ?
            ORDER BY fecha_subida DESC
        ''', (placa,))
        
        rows = cursor.fetchall()
        conn.close()
        
        result = [dict(row) for row in rows]
        logger.info(f"📋 Evidencias encontradas para {placa}: {len(result)}")
        
        return result
    except Exception as e:
        logger.error(f"❌ Error obteniendo URLs de BD: {e}")
        return []

def eliminar_url_evidencia(placa: str, filename: str):
    """Elimina una URL de evidencia de la base de datos"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM evidencias_urls
            WHERE placa = ? AND filename = ?
        ''', (placa, filename))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted > 0:
            logger.info(f"✓ URL eliminada de BD: {placa} - {filename}")
            return True
        else:
            logger.warning(f"⚠️ No se encontró URL en BD: {placa} - {filename}")
            return False
    except Exception as e:
        logger.error(f"❌ Error eliminando URL de BD: {e}")
        return False

# ========= FUNCIONES AUXILIARES =========

def normaliza_texto(texto):
    if not texto:
        return ""
    return str(texto).strip().upper()

def normaliza_placa(placa):
    if not placa:
        return ""
    placa_norm = str(placa).replace(" ", "").replace("-", "").replace("_", "")
    placa_norm = placa_norm.strip().lstrip("0").upper()
    return placa_norm if placa_norm else "0"

def detectar_columna(headers, palabras_clave):
    headers_lower = [h.lower().strip() for h in headers]
    for idx, header in enumerate(headers_lower):
        for palabra in palabras_clave:
            if palabra.lower() in header:
                return idx
    return None

def get_google_sheet_data():
    """Función original de carga de Google Sheets (sin cambios)"""
    try:
        load_dotenv()
        sheet_id = os.getenv("GOOGLE_SHEET_ID")
        creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")

        if not sheet_id:
            logger.error("GOOGLE_SHEET_ID no configurado en .env")
            return [{"id": "ERROR", "placa": "ERROR", "nombre": "GOOGLE_SHEET_ID no configurado"}]

        if not os.path.exists(creds_path):
            logger.error(f"Archivo de credenciales no encontrado: {creds_path}")
            return [{"id": "ERROR", "placa": "ERROR", "nombre": "Credenciales no encontradas"}]

        logger.info("📥 Conectando a Google Sheets...")

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly"
        ]

        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_id)

        logger.info(f"✅ Conectado exitosamente a: {sheet.title}")

        articles = []
        total_sheets = 0
        total_rows_processed = 0

        for ws in sheet.worksheets():
            total_sheets += 1
            sheet_name = ws.title

            try:
                rows = ws.get_all_values()
                if len(rows) <= 1:
                    logger.warning(f"Hoja '{sheet_name}' vacía o solo con encabezados")
                    continue

                headers = rows[0]
                logger.info(f"Procesando hoja: '{sheet_name}' ({len(rows) - 1} filas)")

                col_map = {
                    "placa": detectar_columna(headers, ["placa", "código", "codigo", "id", "identificador"]),
                    "descripcion": detectar_columna(headers, ["descripción", "descripcion", "descripcion actual", "artículo", "articulo", "nombre"]),
                    "marca": detectar_columna(headers, ["marca", "fabricante"]),
                    "modelo": detectar_columna(headers, ["modelo", "model"]),
                    "valor": detectar_columna(headers, ["valor", "precio", "valor ingreso", "costo"]),
                    "fecha": detectar_columna(headers, ["fecha", "fecha adquisición", "fecha adquisicion", "fecha compra"]),
                    "ubicacion": detectar_columna(headers, ["ubicación", "ubicacion", "lugar", "sitio"]),
                    "responsable": detectar_columna(headers, ["responsable", "responsable actual", "origen", "custodio", "encargado"])
                }

                mapeo_log = {k: headers[v] if v is not None else "N/A" for k, v in col_map.items()}
                logger.info(f"Mapeo de columnas para '{sheet_name}': {mapeo_log}")

                for row_idx, row in enumerate(rows[1:], start=2):
                    while len(row) < len(headers):
                        row.append("")

                    placa_idx = col_map.get("placa")
                    if placa_idx is None or placa_idx >= len(row):
                        continue

                    placa = row[placa_idx].strip()
                    if not placa:
                        continue

                    descripcion = row[col_map["descripcion"]].strip() if col_map.get("descripcion") is not None and col_map["descripcion"] < len(row) else ""
                    marca = row[col_map["marca"]].strip() if col_map.get("marca") is not None and col_map["marca"] < len(row) else ""
                    modelo = row[col_map["modelo"]].strip() if col_map.get("modelo") is not None and col_map["modelo"] < len(row) else ""

                    nombre_parts = []
                    if descripcion and descripcion.upper() not in ["NA", "N/A", "N.A.", ""]:
                        nombre_parts.append(descripcion)
                    if marca and marca.upper() not in ["NA", "N/A", "N.A.", "", "SIN MARCA"]:
                        nombre_parts.append(marca)
                    if modelo and modelo.upper() not in ["NA", "N/A", "N.A.", "", "SIN MODELO"]:
                        nombre_parts.append(modelo)

                    nombre = " ".join(nombre_parts) if nombre_parts else f"Artículo {placa}"

                    valor = 0.0
                    if col_map.get("valor") is not None and col_map["valor"] < len(row):
                        valor_str = re.sub(r"[^0-9.]", "", row[col_map["valor"]])
                        try:
                            valor = float(valor_str) if valor_str else 0.0
                        except Exception:
                            valor = 0.0

                    fecha = ""
                    if col_map.get("fecha") is not None and col_map["fecha"] < len(row):
                        fecha = row[col_map["fecha"]].strip()

                    ubicacion = "SENA"
                    if col_map.get("ubicacion") is not None and col_map["ubicacion"] < len(row):
                        ubicacion_raw = row[col_map["ubicacion"]].strip()
                        if ubicacion_raw and ubicacion_raw.upper() not in ["NA", "N/A", "N.A.", ""]:
                            ubicacion = ubicacion_raw

                    responsable = sheet_name
                    if col_map.get("responsable") is not None and col_map["responsable"] < len(row):
                        responsable_raw = row[col_map["responsable"]].strip()
                        if responsable_raw and responsable_raw.upper() not in ["NA", "N/A", "N.A.", ""]:
                            responsable = responsable_raw

                    def valor_o_vacio(header_name, row_, headers_):
                        try:
                            idx = headers_.index(header_name)
                            val = row_[idx].strip()
                            return val if val else "Sin información"
                        except Exception:
                            return "Sin información"

                    articulo = {
                        "placa": placa,
                        "placa_normalizada": normaliza_placa(placa),
                        "Centro": valor_o_vacio("Centro", row, headers),
                        "Modelo": valor_o_vacio("Modelo", row, headers),
                        "Consec.": valor_o_vacio("Consec.", row, headers),
                        "Desc.": valor_o_vacio("Desc.", row, headers),
                        "Descripción Actual": valor_o_vacio("Descripción Actual", row, headers),
                        "Placa": valor_o_vacio("Placa", row, headers),
                        "Atributos": valor_o_vacio("Atributos", row, headers),
                        "Fecha Adquisición": valor_o_vacio("Fecha Adquisición", row, headers),
                        "Ubicación": valor_o_vacio("Ubicación", row, headers),
                        "Evidencias": valor_o_vacio("Evidencias", row, headers),
                        "Origen": valor_o_vacio("Origen", row, headers),
                        "valor": valor,
                        "fecha_adquisicion": fecha,
                        "ubicacion": ubicacion,
                        "responsable": responsable,
                        "hoja": sheet_name,
                        "fila": row_idx,
                        "nombre": nombre,
                        "categoria": descripcion or "Sin categoría",
                    }

                    articulo["placa"] = articulo.get("Placa", "").strip()
                    articulo["consec"] = articulo.get("Consec.", "").strip()
                    articulo["responsable"] = articulo.get("Origen", "").strip() or responsable

                    articles.append(articulo)
                    total_rows_processed += 1

            except Exception as e:
                logger.error(f"Error procesando hoja '{sheet_name}': {e}")
                continue

        logger.info(f"✅ Procesamiento completado: {total_rows_processed} artículos de {total_sheets} hojas")

        if not articles:
            return [{"id": "EMPTY", "placa": "EMPTY", "nombre": "No se encontraron artículos"}]

        return articles

    except gspread.exceptions.SpreadsheetNotFound:
        logger.error("Google Sheet no encontrado. Verifica el ID y los permisos.")
        return [{"id": "ERROR", "placa": "ERROR", "nombre": "Hoja no encontrada o sin permisos"}]

    except Exception as e:
        logger.error(f"Error general: {type(e).__name__}: {e}")
        return [{"id": "ERROR", "placa": "ERROR", "nombre": f"Error: {str(e)}"}]

# ========= NUEVA FUNCIÓN: CACHE INTELIGENTE =========

def get_cached_data(force_refresh=False):
    """
    Obtiene datos con cache inteligente en RAM
    
    - force_refresh: Fuerza recarga desde Google Sheets
    - Thread-safe con Lock
    - Avisa cuando cache está expirado
    """
    global _cache, _cache_timestamp
    
    with _cache_lock:
        # Si se fuerza refresh o no hay cache
        if force_refresh or _cache is None or _cache_timestamp is None:
            logger.info("📥 Cargando datos desde Google Sheets...")
            _cache = get_google_sheet_data()
            _cache_timestamp = datetime.now()
            logger.info(f"✅ Cache actualizado: {len(_cache)} artículos")
            return _cache
        
        # Verificar antigüedad del cache
        elapsed = (datetime.now() - _cache_timestamp).total_seconds()
        if elapsed > CACHE_TTL:
            logger.warning(f"⚠️ Cache expirado ({int(elapsed)}s / {CACHE_TTL}s). Usar /api/inventario/refresh para actualizar")
        
        return _cache

# ========= CARGA ASÍNCRONA INICIAL =========

async def load_initial_cache():
    """Carga inicial de cache en segundo plano"""
    await asyncio.sleep(2)  # Dar tiempo a que el servidor inicie
    logger.info("🔄 Cargando cache inicial en background...")
    get_cached_data(force_refresh=True)

# ========= EVENTOS DE INICIO - OPTIMIZADO =========

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Iniciando Sistema Inventario SENA v3.0.3-OPTIMIZADO-RAM...")
    init_database()
    
    # Cargar cache en background (no bloquea arranque)
    asyncio.create_task(load_initial_cache())
    logger.info("✅ Sistema listo - Cache cargándose en segundo plano")

# ========= RUTA RAÍZ =========

@app.get("/")
async def root():
    """Ruta raíz - retorna el frontend"""
    try:
        return FileResponse("../frontend/admin.html")
    except Exception:
        return {
            "message": "Sistema Inventario SENA v3.0.3-OPTIMIZADO-RAM",
            "status": "online",
            "timestamp": datetime.now().isoformat()
        }

# Ruta explícita para servir el panel de administración
@app.get("/admin.html")
async def admin_html():
    try:
        return FileResponse("../frontend/admin.html")
    except Exception as e:
        logger.error(f"No se pudo servir admin.html: {e}")
        raise HTTPException(status_code=404, detail="admin.html no encontrado")

# ========= ENDPOINTS PARA EVIDENCIAS =========

@app.post("/api/inventario/{placa}/evidencia")
async def subir_evidencia(placa: str, file: UploadFile = File(...)):
    """Guarda una imagen de evidencia en disco local y BD SQLite"""
    safe_name = file.filename.replace(" ", "_")
    filename = f"{placa}_{safe_name}"
    save_path = os.path.join(EVIDENCIAS_DIR, filename)

    try:
        with open(save_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"✓ Archivo guardado en disco: {save_path}")
        
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        public_url = f"{base_url}/evidencias/{filename}"
        
        logger.info(f"📍 URL generada: {public_url}")
        
        guardado = guardar_url_evidencia(placa, public_url, filename)
        
        if not guardado:
            logger.error("❌ FALLO AL GUARDAR EN BASE DE DATOS")
            raise HTTPException(
                status_code=500, 
                detail="Archivo guardado pero falló el registro en base de datos"
            )
        
        logger.info(f"✅ EVIDENCIA COMPLETA: {filename} para placa {placa}")
        
        return {
            "url": public_url,
            "filename": filename,
            "message": "Evidencia guardada correctamente",
            "guardado_bd": True
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error guardando evidencia para placa {placa}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error al guardar la evidencia: {str(e)}")

@app.get("/api/inventario/{placa}/evidencias")
async def obtener_evidencias(placa: str):
    """Obtiene todas las URLs de evidencias almacenadas para una placa"""
    try:
        urls = obtener_urls_evidencias(placa)
        
        return {
            "placa": placa,
            "total": len(urls),
            "evidencias": urls
        }
    except Exception as e:
        logger.error(f"Error obteniendo evidencias de {placa}: {e}")
        raise HTTPException(status_code=500, detail="Error al obtener evidencias")

@app.delete("/api/inventario/{placa}/evidencia/{filename}")
async def eliminar_evidencia(placa: str, filename: str):
    """Elimina una evidencia del disco y de la base de datos"""
    try:
        file_path = os.path.join(EVIDENCIAS_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"✓ Archivo eliminado del disco: {filename}")
        
        eliminar_url_evidencia(placa, filename)
        
        return {
            "message": "Evidencia eliminada correctamente",
            "placa": placa,
            "filename": filename
        }
    except Exception as e:
        logger.error(f"Error eliminando evidencia {filename}: {e}")
        raise HTTPException(status_code=500, detail="Error al eliminar evidencia")

@app.put("/api/inventario/{placa}/sincronizar-evidencias")
async def sincronizar_evidencias_google_sheets(placa: str):
    """Sincroniza las URLs de evidencias almacenadas en SQLite con Google Sheets"""
    try:
        urls = obtener_urls_evidencias(placa)
        
        if not urls:
            raise HTTPException(404, "No hay evidencias para sincronizar")
        
        urls_text = ", ".join([u["url"] for u in urls])
        
        load_dotenv()
        sheet_id = os.getenv("GOOGLE_SHEET_ID")
        creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open_by_key(sheet_id)
        
        encontrado = False
        
        for ws in sheet.worksheets():
            rows = ws.get_all_values()
            if not rows:
                continue
            
            headers = rows[0]
            if "Placa" not in headers or "Evidencias" not in headers:
                continue
            
            placa_idx = headers.index("Placa")
            evidencias_idx = headers.index("Evidencias") + 1
            
            for idx, row in enumerate(rows[1:], start=2):
                if placa_idx >= len(row):
                    continue
                
                if row[placa_idx].strip() == placa:
                    ws.update_cell(idx, evidencias_idx, urls_text)
                    encontrado = True
                    break
            
            if encontrado:
                break
        
        if not encontrado:
            raise HTTPException(404, f"Artículo con placa '{placa}' no encontrado en Google Sheets")
        
        # ✅ USAR CACHE OPTIMIZADO
        get_cached_data(force_refresh=True)
        
        return {
            "message": "Evidencias sincronizadas con Google Sheets",
            "placa": placa,
            "total_urls": len(urls),
            "urls_sincronizadas": urls_text
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sincronizando evidencias: {e}")
        raise HTTPException(status_code=500, detail=f"Error en sincronización: {str(e)}")

# ========= ENDPOINT DEBUG =========

@app.get("/api/debug/evidencias")
async def debug_evidencias():
    """Endpoint de depuración"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        cursor.execute("SELECT COUNT(*) FROM evidencias_urls")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT * FROM evidencias_urls ORDER BY fecha_subida DESC LIMIT 10")
        registros = cursor.fetchall()
        
        conn.close()
        
        return {
            "db_path": DB_PATH,
            "db_exists": os.path.exists(DB_PATH),
            "db_size": os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0,
            "tables": tables,
            "total_registros": total,
            "ultimos_10": registros
        }
    except Exception as e:
        return {
            "error": str(e),
            "db_path": DB_PATH,
            "db_exists": os.path.exists(DB_PATH)
        }

# ========= ENDPOINTS CRUD - OPTIMIZADOS =========

@app.post("/api/inventario/crear")
async def crear_articulo(articulo: dict = Body(...)):
    responsable = articulo.get("responsable") or articulo.get("Origen")
    if not responsable:
        raise HTTPException(400, "Falta campo 'responsable' o 'Origen'.")
    
    load_dotenv()
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(sheet_id)
    
    try:
        ws = sheet.worksheet(responsable)
    except Exception:
        ws = sheet.add_worksheet(title=responsable, rows="1000", cols="20")
    
    row = [
        articulo.get("Centro", ""),
        articulo.get("Modelo", ""),
        articulo.get("Consec.", ""),
        articulo.get("Desc", articulo.get("Desc.", "")),
        articulo.get("Descripción Actual", ""),
        articulo.get("Placa", ""),
        articulo.get("Atributos", ""),
        articulo.get("Fecha Adquisición", ""),
        articulo.get("Ubicación", ""),
        articulo.get("Evidencias", ""),
        articulo.get("Origen", responsable)
    ]
    ws.append_row(row)
    
    # ✅ USAR CACHE OPTIMIZADO
    get_cached_data(force_refresh=True)
    return {"message": "Artículo creado correctamente"}

@app.put("/api/inventario/{placa}/editar")
async def editar_articulo(placa: str, datos_actualizados: dict = Body(...)):
    """Actualiza SOLO las columnas indicadas en datos_actualizados"""
    load_dotenv()
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(sheet_id)

    encontrado = False

    campos_a_columnas = {
        "Centro": "Centro",
        "Modelo": "Modelo",
        "Consec.": "Consec.",
        "Desc.": "Desc.",
        "Descripción Actual": "Descripción Actual",
        "Placa": "Placa",
        "Atributos": "Atributos",
        "Fecha Adquisición": "Fecha Adquisición",
        "Ubicación": "Ubicación",
        "Evidencias": "Evidencias",
        "Origen": "Origen",
    }

    for ws in sheet.worksheets():
        rows = ws.get_all_values()
        if not rows:
            continue

        headers = rows[0]

        if "Placa" not in headers:
            continue

        placa_idx = headers.index("Placa")

        for idx, row in enumerate(rows[1:], start=2):
            if placa_idx >= len(row):
                continue

            if row[placa_idx].strip() == placa:
                for campo_json, nombre_col in campos_a_columnas.items():
                    if campo_json in datos_actualizados and nombre_col in headers:
                        col_idx = headers.index(nombre_col) + 1
                        nuevo_valor = datos_actualizados.get(campo_json, "")
                        ws.update_cell(idx, col_idx, nuevo_valor)
                encontrado = True
                break

        if encontrado:
            break

    if not encontrado:
        raise HTTPException(404, f"Artículo con placa '{placa}' no encontrado")

    # ✅ USAR CACHE OPTIMIZADO
    get_cached_data(force_refresh=True)
    return {"message": "Artículo editado correctamente"}

@app.delete("/api/inventario/{placa}/eliminar")
async def eliminar_articulo(placa: str):
    load_dotenv()
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(sheet_id)
    
    encontrado = False
    for ws in sheet.worksheets():
        rows = ws.get_all_values()
        if not rows:
            continue
        headers = rows[0]
        if "Placa" not in headers:
            continue
        placa_idx = headers.index("Placa")
        for idx, row in enumerate(rows[1:], start=2):
            if placa_idx >= len(row):
                continue
            if row[placa_idx].strip() == placa:
                ws.delete_rows(idx)
                encontrado = True
                break
        if encontrado:
            break
    
    if not encontrado:
        raise HTTPException(404, f"Artículo con placa '{placa}' no encontrado")
    
    # ✅ USAR CACHE OPTIMIZADO
    get_cached_data(force_refresh=True)
    return {"message": f"Artículo con placa {placa} eliminado correctamente"}

# ========= ENDPOINTS GET - OPTIMIZADOS CON CACHE =========

@app.get("/api/health")
async def health_check():
    global _cache, _cache_timestamp
    
    cache_age = None
    if _cache_timestamp:
        cache_age = int((datetime.now() - _cache_timestamp).total_seconds())
    
    return {
        "status": "healthy",
        "version": "3.0.3-OPTIMIZADO-RAM",
        "cache_size": len(_cache) if _cache else 0,
        "cache_timestamp": _cache_timestamp.isoformat() if _cache_timestamp else None,
        "cache_age_seconds": cache_age,
        "cache_ttl_seconds": CACHE_TTL,
        "cache_expired": cache_age > CACHE_TTL if cache_age else False,
        "timestamp": datetime.now().isoformat(),
        "db_path": DB_PATH,
        "db_exists": os.path.exists(DB_PATH)
    }

@app.get("/api/articulos")
async def api_articulos():
    # ✅ USAR CACHE OPTIMIZADO
    articulos = get_cached_data()
    return {"articulos": articulos, "total": len(articulos)}

@app.get("/api/inventario/consulta")
async def consulta_inventario(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    placa: str = None,
    consecutivo: str = None,
    responsable: str = None,
    fecha_inicio: str = None,
    fecha_fin: str = None,
    exportar_todo: bool = Query(False)
):
    # ✅ USAR CACHE OPTIMIZADO
    articulos = get_cached_data()

    placa_norm = placa.upper() if placa else None
    consecutivo_norm = consecutivo.upper() if consecutivo else None
    resp_norm = responsable.upper() if responsable else None

    fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d") if fecha_inicio else datetime.min
    fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d") if fecha_fin else datetime.max

    def filtro(art):
        if fecha_inicio or fecha_fin:
            fecha_art_str = art.get("Fecha Adquisición", "")
            if not fecha_art_str:
                return False
            try:
                fecha_art = datetime.strptime(fecha_art_str.split("T")[0], "%d/%m/%Y")
            except ValueError:
                try:
                    fecha_art = datetime.strptime(fecha_art_str.split("T")[0], "%Y-%m-%d")
                except ValueError:
                    return False
            if fecha_art < fecha_inicio_dt or fecha_art > fecha_fin_dt:
                return False

        if placa_norm and placa_norm not in art.get("placa", "").upper():
            return False
        if consecutivo_norm and consecutivo_norm not in art.get("consec", "").upper():
            return False
        if resp_norm and resp_norm != art.get("responsable", "").upper().strip():
            return False
        return True

    articulos_filtrados = list(filter(filtro, articulos))
    total = len(articulos_filtrados)

    if exportar_todo:
        return {
            "articulos": articulos_filtrados,
            "total": total,
            "page": 1,
            "limit": total,
            "total_pages": 1,
        }

    start = (page - 1) * limit
    end = start + limit
    return {
        "articulos": articulos_filtrados[start:end],
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit,
    }

@app.get("/api/inventario/categorias")
async def get_categorias():
    # ✅ USAR CACHE OPTIMIZADO
    articulos = get_cached_data()
    categorias = sorted(set(
        art.get("categoria", "")
        for art in articulos
        if art.get("categoria") and art.get("categoria") not in ["", "ERROR", "EMPTY"]
    ))
    return categorias

@app.get("/api/inventario/responsables")
async def get_responsables():
    # ✅ USAR CACHE OPTIMIZADO
    articulos = get_cached_data()
    responsables = sorted(set(
        art.get("responsable", "")
        for art in articulos
        if art.get("responsable") and art.get("responsable") not in ["", "ERROR", "EMPTY"]
    ))
    return responsables

@app.get("/api/inventario/estadisticas")
async def get_estadisticas():
    # ✅ USAR CACHE OPTIMIZADO
    articulos = get_cached_data()
    articulos_validos = [a for a in articulos if a.get("placa") not in ["ERROR", "EMPTY"]]
    return {
        "total_articulos": len(articulos_validos),
        "hojas_procesadas": len(set(art.get("hoja", "") for art in articulos_validos)),
        "valor_total": sum(art.get("valor", 0) for art in articulos_validos),
        "categorias_unicas": len(set(art.get("categoria", "") for art in articulos_validos if art.get("categoria"))),
        "responsables_unicos": len(set(art.get("responsable", "") for art in articulos_validos if art.get("responsable")))
    }

@app.get("/api/inventario/{placa}/detalle")
async def detalle_articulo(placa: str):
    # ✅ USAR CACHE OPTIMIZADO
    articulos = get_cached_data()
    placa_norm = normaliza_placa(placa)
    logger.info(f"Buscando detalle para placa: '{placa}' (normalizada: '{placa_norm}')")

    for art in articulos:
        art_placa_norm = normaliza_placa(art.get("placa", ""))
        if art_placa_norm == placa_norm:
            logger.info(f"✓ Detalle encontrado: {art.get('nombre')}")
            return {"articulo": art}

    for art in articulos:
        if art.get("placa", "").strip() == placa.strip():
            logger.info(f"✓ Detalle encontrado (búsqueda original): {art.get('nombre')}")
            return {"articulo": art}

    logger.warning(f"✗ Placa no encontrada: '{placa}'")
    raise HTTPException(404, f"Artículo con placa '{placa}' no encontrado")

@app.post("/api/inventario/refresh")
async def refresh_cache():
    """ENDPOINT PARA REFRESCAR CACHE MANUALMENTE"""
    logger.info("🔄 Refrescando cache manualmente...")
    articulos = get_cached_data(force_refresh=True)
    
    global _cache_timestamp
    return {
        "message": "✅ Cache actualizado exitosamente",
        "total_articulos": len(articulos),
        "timestamp": _cache_timestamp.isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
