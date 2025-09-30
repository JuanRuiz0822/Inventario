# SOLUCIÓN SIMPLE - APP.PY SIN SQLALCHEMY
# Crear versión simplificada sin dependencias complejas

# Importaciones simples - solo lo esencial
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles  
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional, List
from datetime import datetime
import os
import re
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# Crear aplicación FastAPI
app = FastAPI(
    title="Sistema de Inventario SENA",
    description="Sistema de gestión de inventario conectado con Google Sheets",
    version="2.1.0"
)

# Servir archivos estáticos
try:
    app.mount("/static", StaticFiles(directory="frontend"), name="static")
except:
    print("⚠️ Directorio frontend no encontrado")

# Función principal para obtener datos de Google Sheets
def get_google_sheet_data():
    """Obtener TODOS los datos reales de Google Sheets"""
    try:
        print("🔍 Conectando con Google Sheets...")
        
        # Cargar variables de entorno
        if os.path.exists('../.env'):
            load_dotenv('../.env')
        elif os.path.exists('.env'):
            load_dotenv('.env')
        
        sheet_id = os.getenv('GOOGLE_SHEET_ID', '1tCILvM3VkaACJMNnTZu4ZYM3x81HcoTlg6uoj-K6RRQ')
        credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'credentials.json')
        
        # Verificar credenciales
        if not os.path.exists(credentials_path):
            print(f"❌ Credenciales no encontradas: {credentials_path}")
            return generar_datos_ejemplo_minimo()
        
        # Configurar Google Sheets API
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets.readonly",
            "https://www.googleapis.com/auth/drive.readonly"
        ]
        
        creds = Credentials.from_service_account_file(credentials_path, scopes=scopes)
        client = gspread.authorize(creds)
        
        # Abrir Google Sheet
        sheet = client.open_by_key(sheet_id)
        print(f"✅ Sheet abierto: {sheet.title}")
        
        # Procesar todas las hojas
        articulos_totales = []
        hojas_procesadas = 0
        
        for worksheet in sheet.worksheets():
            try:
                print(f"📊 Procesando hoja: {worksheet.title}")
                
                # Obtener todos los valores
                all_values = worksheet.get_all_values()
                
                if len(all_values) <= 1:
                    print(f"   ⚠️ Hoja {worksheet.title} vacía")
                    continue
                
                headers = all_values[0]
                data_rows = all_values[1:]
                
                print(f"   📈 Procesando {len(data_rows)} filas...")
                articulos_hoja = 0
                
                # Procesar cada fila
                for i, row in enumerate(data_rows):
                    try:
                        # Asegurar columnas suficientes
                        while len(row) < len(headers):
                            row.append("")
                        
                        # Crear diccionario
                        row_dict = {}
                        for j, header in enumerate(headers):
                            if j < len(row):
                                row_dict[header] = row[j]
                            else:
                                row_dict[header] = ""
                        
                        # Extraer placa
                        placa = str(row_dict.get("Placa", "")).strip()
                        
                        # Filtro permisivo para placas
                        if not placa or placa.lower() in ['', 'nan', 'none', 'null', 'placa']:
                            continue
                        
                        # Extraer datos principales
                        desc_actual = str(row_dict.get("Descripción Actual", "")).strip()
                        marca = str(row_dict.get("Marca", "")).strip()
                        modelo = str(row_dict.get("Modelo", "")).strip()
                        
                        # Construir nombre
                        nombre = desc_actual
                        if marca and marca.upper() not in ['NA', 'N/A', '.', 'NAN', '']:
                            nombre += f" {marca}"
                        if modelo and modelo.upper() not in ['NA', 'N/A', '.', 'NAN', '']:
                            nombre += f" {modelo}"
                        
                        # Valor monetario
                        valor_str = str(row_dict.get("Valor Ingreso", "0"))
                        valor_limpio = re.sub(r'[^0-9.,]', '', valor_str.replace(',', ''))
                        try:
                            valor_num = float(valor_limpio) if valor_limpio else 0
                        except:
                            valor_num = 0
                        
                        # Responsable
                        responsable = "Sin asignar"
                        campos_resp = ["Centro/R", "Responsable", "Custodio", "Usuario"]
                        
                        for campo in campos_resp:
                            if campo in row_dict and row_dict[campo].strip():
                                resp_texto = str(row_dict[campo]).strip()
                                if resp_texto not in ['76,922710', '76.922710', '', 'NA', 'N/A']:
                                    responsable = resp_texto
                                    break
                        
                        # Buscar nombres conocidos si no encontró responsable
                        if responsable == "Sin asignar":
                            nombres_conocidos = [
                                "ALVAREZ DIAZ JUAN GONZALO",
                                "MANTILLA ARENAS WILLIAM", 
                                "ALEXANDER ZAPATA TORO",
                                "LOPEZ HERRERA OSCAR ANTONIO",
                                "DOSSMAN MARQUEZ NOHORA LILIANA",
                                "ARIAS FIGUEROA JAIME DIEGO"
                            ]
                            
                            fila_completa = " ".join(str(v) for v in row_dict.values()).upper()
                            for nombre_conocido in nombres_conocidos:
                                if any(parte in fila_completa for parte in nombre_conocido.split()):
                                    responsable = nombre_conocido
                                    break
                        
                        # Crear artículo
                        articulo = {
                            "id": placa,
                            "placa": placa,
                            "nombre": nombre.strip() or desc_actual or "Artículo",
                            "marca": marca if marca.upper() not in ['NA', 'N/A', 'NAN', ''] else "",
                            "modelo": modelo if modelo.upper() not in ['NA', 'N/A', 'NAN', ''] else "",
                            "categoria": desc_actual or "Sin categoría",
                            "descripcion": str(row_dict.get("Atributos", desc_actual)).strip() or desc_actual,
                            "valor": f"{valor_num:,.2f}",
                            "fecha_adquisicion": str(row_dict.get("Fecha Adquisición", "")).strip(),
                            "ubicacion": str(row_dict.get("Ubicación", "SENA")).strip(),
                            "responsable": responsable,
                            "observaciones": str(row_dict.get("Observaciones", "")).strip(),
                            "consecutivo": str(row_dict.get("Consec.", "")).strip(),
                            "tipo_elemento": str(row_dict.get("Tipo", "")).strip(),
                            "hoja_origen": worksheet.title,
                            "estado": "Activo",
                            "fecha_actualizacion": datetime.now().isoformat()
                        }
                        
                        articulos_totales.append(articulo)
                        articulos_hoja += 1
                        
                    except Exception as e:
                        print(f"   ⚠️ Error fila {i+1}: {e}")
                        continue
                
                print(f"   ✅ {articulos_hoja} artículos procesados de {worksheet.title}")
                hojas_procesadas += 1
                
            except Exception as e:
                print(f"   ❌ Error procesando hoja {worksheet.title}: {e}")
                continue
        
        print(f"🎉 PROCESAMIENTO COMPLETO:")
        print(f"   📊 {hojas_procesadas} hojas procesadas")
        print(f"   📋 {len(articulos_totales)} artículos totales")
        
        if not articulos_totales:
            print("⚠️ No se encontraron artículos válidos")
            return generar_datos_ejemplo_minimo()
        
        return articulos_totales
        
    except Exception as e:
        print(f"❌ Error general: {e}")
        return generar_datos_ejemplo_minimo()

def generar_datos_ejemplo_minimo():
    """Datos de ejemplo si falla la conexión"""
    return [
        {
            "id": "ERROR_CONEXION",
            "placa": "ERROR_CONEXION",
            "nombre": "⚠️ ERROR DE CONEXIÓN CON GOOGLE SHEETS",
            "marca": "SISTEMA",
            "modelo": "ERROR",
            "categoria": "ERROR DE CONEXIÓN",
            "descripcion": "No se pudo conectar con Google Sheets. Verificar credenciales.",
            "valor": "0.00",
            "fecha_adquisicion": "2025-01-01",
            "ubicacion": "Sistema",
            "responsable": "ADMINISTRADOR SISTEMA",
            "observaciones": "Revisar configuración de Google Sheets API",
            "consecutivo": "000",
            "tipo_elemento": "ERROR",
            "hoja_origen": "Sistema",
            "estado": "Error",
            "fecha_actualizacion": datetime.now().isoformat()
        }
    ]

# Variable global para cachear datos
_articulos_cache = None
_cache_timestamp = None

def get_articulos_cached():
    """Obtener artículos con cache simple"""
    global _articulos_cache, _cache_timestamp
    
    # Cache por 5 minutos
    if _articulos_cache is None or _cache_timestamp is None or \
       (datetime.now().timestamp() - _cache_timestamp) > 300:
        
        print("🔄 Actualizando cache de artículos...")
        _articulos_cache = get_google_sheet_data()
        _cache_timestamp = datetime.now().timestamp()
    
    return _articulos_cache

# ============================================
# ENDPOINTS DE LA API
# ============================================

@app.get("/")
async def root():
    """Página principal"""
    try:
        return FileResponse("frontend/admin.html")
    except:
        return {"message": "Sistema de Inventario SENA", "status": "operativo", "timestamp": datetime.now().isoformat()}

@app.get("/admin.html")  
async def admin():
    """Panel administrativo"""
    try:
        return FileResponse("frontend/admin.html")
    except:
        return {"message": "Panel administrativo - usar /api/articulos para datos"}

@app.get("/health")
async def health():
    """Estado del sistema"""
    return {
        "status": "ok", 
        "timestamp": datetime.now().isoformat(),
        "version": "2.1.0"
    }

@app.get("/api/articulos")
async def get_articulos():
    """Obtener todos los artículos"""
    try:
        articulos = get_articulos_cached()
        return {
            "articulos": articulos,
            "total": len(articulos),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"❌ Error en /api/articulos: {e}")
        return {
            "error": str(e), 
            "articulos": [],
            "total": 0
        }

@app.get("/api/inventario/consulta")
async def consulta_inventario(
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(50, ge=1, le=500, description="Artículos por página"),
    busqueda: Optional[str] = Query(None, description="Término de búsqueda"),
    categoria: Optional[str] = Query(None, description="Filtrar por categoría"),
    responsable: Optional[str] = Query(None, description="Filtrar por responsable")
):
    """Consulta paginada con filtros"""
    try:
        # Obtener artículos
        todos_articulos = get_articulos_cached()
        articulos_filtrados = todos_articulos.copy()
        
        # Aplicar filtro de búsqueda
        if busqueda and busqueda.strip():
            busqueda_lower = busqueda.lower().strip()
            articulos_filtrados = [
                art for art in articulos_filtrados 
                if (busqueda_lower in art.get('nombre', '').lower() or 
                    busqueda_lower in art.get('placa', '').lower() or
                    busqueda_lower in art.get('descripcion', '').lower() or
                    busqueda_lower in art.get('marca', '').lower())
            ]
        
        # Filtro por categoría
        if categoria and categoria.strip():
            categoria_lower = categoria.lower().strip()
            articulos_filtrados = [
                art for art in articulos_filtrados 
                if categoria_lower in art.get('categoria', '').lower()
            ]
        
        # Filtro por responsable
        if responsable and responsable.strip():
            responsable_lower = responsable.lower().strip()
            articulos_filtrados = [
                art for art in articulos_filtrados 
                if responsable_lower in art.get('responsable', '').lower()
            ]
        
        # Paginación
        total = len(articulos_filtrados)
        start_idx = (page - 1) * limit
        end_idx = start_idx + limit
        articulos_pagina = articulos_filtrados[start_idx:end_idx]
        
        return {
            "articulos": articulos_pagina,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit if total > 0 else 0,
            "filtros_aplicados": {
                "busqueda": busqueda,
                "categoria": categoria, 
                "responsable": responsable
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error en consulta: {e}")
        return {
            "error": str(e),
            "articulos": [],
            "total": 0,
            "page": page,
            "limit": limit,
            "total_pages": 0
        }

@app.get("/api/inventario/estadisticas")
async def get_estadisticas():
    """Estadísticas completas del inventario"""
    try:
        articulos = get_articulos_cached()
        
        if not articulos or len(articulos) == 0:
            return {"error": "No hay datos disponibles para estadísticas"}
        
        # Estadísticas básicas
        total_articulos = len(articulos)
        valor_total = sum(float(str(art.get('valor', '0')).replace(',', '')) for art in articulos if art.get('valor'))
        
        # Agrupar por categorías
        categorias = {}
        for art in articulos:
            cat = art.get('categoria', 'Sin categoría')[:50]  # Limitar longitud
            categorias[cat] = categorias.get(cat, 0) + 1
        
        top_categorias = [
            {"categoria": cat, "cantidad": cant} 
            for cat, cant in sorted(categorias.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        # Agrupar por responsables
        responsables = {}
        for art in articulos:
            resp = art.get('responsable', 'Sin asignar')[:50]  # Limitar longitud
            responsables[resp] = responsables.get(resp, 0) + 1
        
        top_responsables = [
            {"responsable": resp, "cantidad": cant}
            for resp, cant in sorted(responsables.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        # Agrupar por ubicación
        ubicaciones = {}
        for art in articulos:
            ubic = art.get('ubicacion', 'No especificado')[:30]
            ubicaciones[ubic] = ubicaciones.get(ubic, 0) + 1
        
        top_ubicaciones = [
            {"ubicacion": ubic, "cantidad": cant}
            for ubic, cant in sorted(ubicaciones.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        return {
            "resumen": {
                "total_articulos": total_articulos,
                "valor_total_inventario": f"{valor_total:,.2f}",
                "total_categorias": len(categorias),
                "total_responsables": len(responsables),
                "total_ubicaciones": len(ubicaciones)
            },
            "top_categorias": top_categorias,
            "top_responsables": top_responsables,
            "top_ubicaciones": top_ubicaciones,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"❌ Error en estadísticas: {e}")
        return {"error": str(e)}

@app.get("/api/inventario/categorias")
async def get_categorias():
    """Obtener lista de categorías únicas"""
    try:
        articulos = get_articulos_cached()
        categorias = list(set(
            art.get('categoria', 'Sin categoría') 
            for art in articulos 
            if art.get('categoria')
        ))
        return sorted(categorias)
    except Exception as e:
        return {"error": str(e), "categorias": []}

@app.get("/api/inventario/responsables") 
async def get_responsables():
    """Obtener lista de responsables únicos"""
    try:
        articulos = get_articulos_cached()
        responsables = list(set(
            art.get('responsable', 'Sin asignar') 
            for art in articulos 
            if art.get('responsable')
        ))
        return sorted(responsables)
    except Exception as e:
        return {"error": str(e), "responsables": []}

@app.post("/api/sync/refresh")
async def refresh_cache():
    """Forzar actualización del cache"""
    global _articulos_cache, _cache_timestamp
    try:
        _articulos_cache = None
        _cache_timestamp = None
        articulos = get_articulos_cached()
        
        return {
            "message": "Cache actualizado exitosamente",
            "total_articulos": len(articulos),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

# Manejo de errores
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"message": "Recurso no encontrado"}
    )

@app.exception_handler(500)
async def server_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"message": "Error interno del servidor"}
    )

# Información de la aplicación
@app.get("/api/info")
async def app_info():
    """Información de la aplicación"""
    return {
        "nombre": "Sistema de Inventario SENA",
        "version": "2.1.0",
        "descripcion": "Sistema simplificado conectado con Google Sheets",
        "endpoints": [
            "/api/articulos",
            "/api/inventario/consulta",
            "/api/inventario/estadisticas", 
            "/api/inventario/categorias",
            "/api/inventario/responsables"
        ],
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Iniciando Sistema de Inventario SENA v2.1.0")
    uvicorn.run(app, host="0.0.0.0", port=8000)