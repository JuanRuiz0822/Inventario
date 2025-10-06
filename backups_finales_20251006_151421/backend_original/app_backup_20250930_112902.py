# Sistema de Inventario SENA - Versión Corregida
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.staticfiles import StaticFiles  
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from pydantic import BaseModel
from typing import Optional, List
import os
import re
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
import pandas as pd

# Configuración de base de datos
DATABASE_URL = "sqlite:///./backend/inventario.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Modelos de base de datos
class Articulo(Base):
    __tablename__ = "articulos"
    
    id = Column(Integer, primary_key=True, index=True)
    placa = Column(String, unique=True, index=True)
    nombre = Column(String, index=True)
    marca = Column(String)
    modelo = Column(String)
    categoria = Column(String, index=True)
    descripcion = Column(Text)
    valor = Column(String)
    fecha_adquisicion = Column(String)
    ubicacion = Column(String)
    responsable = Column(String, index=True)
    observaciones = Column(Text)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    activo = Column(Boolean, default=True)

# Crear tablas
Base.metadata.create_all(bind=engine)

# Schemas Pydantic
class ArticuloBase(BaseModel):
    placa: str
    nombre: str
    marca: Optional[str] = ""
    modelo: Optional[str] = ""
    categoria: Optional[str] = ""
    descripcion: Optional[str] = ""
    valor: Optional[str] = "0"
    fecha_adquisicion: Optional[str] = ""
    ubicacion: Optional[str] = ""
    responsable: Optional[str] = ""
    observaciones: Optional[str] = ""

class ArticuloCreate(ArticuloBase):
    pass

class ArticuloResponse(ArticuloBase):
    id: int
    fecha_creacion: datetime
    activo: bool
    
    class Config:
        from_attributes = True

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Función para obtener datos de Google Sheets
def get_google_sheet_data():
    """Obtener TODOS los datos reales de Google Sheets"""
    try:
        print("🔍 Conectando con Google Sheets...")
        
        # Cargar variables de entorno
        if os.path.exists('.env'):
            load_dotenv()
        
        sheet_id = os.getenv('GOOGLE_SHEET_ID', '1tCILvM3VkaACJMNnTZu4ZYM3x81HcoTlg6uoj-K6RRQ')
        credentials_path = os.getenv('GOOGLE_CREDENTIALS_PATH', 'backend/credentials.json')
        
        # Verificar que existen las credenciales
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
                
                # Procesar cada fila
                for i, row in enumerate(data_rows):
                    try:
                        # Asegurar que la fila tenga suficientes columnas
                        while len(row) < len(headers):
                            row.append("")
                        
                        # Crear diccionario para la fila
                        row_dict = {headers[j]: row[j] if j < len(row) else "" for j in range(len(headers))}
                        
                        # Extraer placa
                        placa = str(row_dict.get("Placa", "")).strip()
                        
                        # Solo incluir registros con placa válida
                        if not placa or placa.lower() in ['', 'nan', 'none', 'null', 'placa']:
                            continue
                        
                        # Extraer datos principales
                        desc_actual = str(row_dict.get("Descripción Actual", "")).strip()
                        marca = str(row_dict.get("Marca", "")).strip()
                        modelo = str(row_dict.get("Modelo", "")).strip()
                        
                        # Construir nombre completo
                        nombre_completo = desc_actual
                        if marca and marca.upper() not in ['NA', 'N/A', '.', 'NAN']:
                            nombre_completo += f" {marca}"
                        if modelo and modelo.upper() not in ['NA', 'N/A', '.', 'NAN']:
                            nombre_completo += f" {modelo}"
                        
                        # Valor monetario
                        valor_bruto = str(row_dict.get("Valor Ingreso", "0"))
                        valor_limpio = re.sub(r'[^0-9.,]', '', valor_bruto.replace(',', ''))
                        try:
                            valor_numerico = float(valor_limpio) if valor_limpio else 0
                        except:
                            valor_numerico = 0
                        
                        # Determinar responsable
                        responsable = "Sin asignar"
                        
                        # Buscar en varios campos posibles
                        campos_responsable = ["Centro/R", "Responsable", "Custodio", "Usuario"]
                        for campo in campos_responsable:
                            if campo in row_dict and row_dict[campo].strip():
                                texto_resp = str(row_dict[campo]).strip()
                                if texto_resp not in ['76,922710', '76.922710', '', 'NA']:
                                    responsable = texto_resp
                                    break
                        
                        # Si no encontró, buscar nombres conocidos
                        if responsable == "Sin asignar":
                            nombres_conocidos = [
                                "ALVAREZ DIAZ JUAN GONZALO",
                                "MANTILLA ARENAS WILLIAM", 
                                "ALEXANDER ZAPATA TORO",
                                "LOPEZ HERRERA OSCAR ANTONIO",
                                "DOSSMAN MARQUEZ NOHORA LILIANA",
                                "ARIAS FIGUEROA JAIME DIEGO"
                            ]
                            
                            fila_texto = " ".join(str(v) for v in row_dict.values()).upper()
                            for nombre in nombres_conocidos:
                                if any(parte in fila_texto for parte in nombre.split()):
                                    responsable = nombre
                                    break
                        
                        # Crear artículo
                        articulo = {
                            "id": placa,
                            "placa": placa,
                            "nombre": nombre_completo.strip() or desc_actual or "Artículo",
                            "marca": marca if marca.upper() not in ['NA', 'N/A', 'NAN'] else "",
                            "modelo": modelo if modelo.upper() not in ['NA', 'N/A', 'NAN'] else "",
                            "categoria": desc_actual or "Sin categoría",
                            "descripcion": str(row_dict.get("Atributos", desc_actual)).strip() or desc_actual,
                            "valor": str(valor_numerico),
                            "fecha_adquisicion": str(row_dict.get("Fecha Adquisición", "")).strip(),
                            "ubicacion": str(row_dict.get("Ubicación", "SENA")).strip(),
                            "responsable": responsable,
                            "observaciones": str(row_dict.get("Observaciones", "")).strip(),
                            "consecutivo": str(row_dict.get("Consec.", "")).strip(),
                            "tipo_elemento": str(row_dict.get("Tipo", "")).strip(),
                            "hoja_origen": worksheet.title
                        }
                        
                        articulos_totales.append(articulo)
                        
                    except Exception as e:
                        print(f"   ⚠️ Error fila {i+1}: {e}")
                        continue
                
                count_hoja = len([a for a in articulos_totales if a.get('hoja_origen') == worksheet.title])
                print(f"   ✅ {count_hoja} artículos procesados de {worksheet.title}")
                
            except Exception as e:
                print(f"   ❌ Error procesando hoja {worksheet.title}: {e}")
                continue
        
        print(f"🎉 TOTAL PROCESADO: {len(articulos_totales)} artículos")
        
        if not articulos_totales:
            print("⚠️ No se encontraron artículos, usando datos mínimos")
            return generar_datos_ejemplo_minimo()
        
        return articulos_totales
        
    except Exception as e:
        print(f"❌ Error general Google Sheets: {e}")
        return generar_datos_ejemplo_minimo()

def generar_datos_ejemplo_minimo():
    """Datos mínimos si Google Sheets falla"""
    return [
        {
            "id": "ERROR_SHEETS",
            "placa": "ERROR_SHEETS",
            "nombre": "⚠️ ERROR CONEXIÓN GOOGLE SHEETS",
            "marca": "SISTEMA",
            "modelo": "ERROR",
            "categoria": "ERROR",
            "descripcion": "Verificar credenciales Google Sheets",
            "valor": "0",
            "fecha_adquisicion": "2025-01-01",
            "ubicacion": "Sistema",
            "responsable": "ADMINISTRADOR",
            "observaciones": "Revisar configuración",
            "consecutivo": "000",
            "tipo_elemento": "ERROR",
            "hoja_origen": "Sistema"
        }
    ]

# Crear aplicación FastAPI
app = FastAPI(
    title="Sistema de Inventario SENA",
    description="Sistema de gestión de inventario conectado con Google Sheets",
    version="2.0.0"
)

# Servir archivos estáticos
try:
    app.mount("/static", StaticFiles(directory="frontend"), name="static")
except:
    print("⚠️ Directorio frontend no encontrado")

# Rutas principales
@app.get("/")
async def root():
    """Página principal"""
    try:
        return FileResponse("frontend/admin.html")
    except:
        return {"message": "Sistema de Inventario SENA", "status": "funcionando"}

@app.get("/admin.html")  
async def admin():
    """Panel administrativo"""
    try:
        return FileResponse("frontend/admin.html")
    except:
        return {"message": "Panel administrativo disponible"}

@app.get("/health")
async def health():
    """Estado del sistema"""
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}

# API Endpoints
@app.get("/api/articulos")
async def get_articulos():
    """Obtener todos los artículos"""
    try:
        articulos = get_google_sheet_data()
        return articulos
    except Exception as e:
        return {"error": str(e), "articulos": []}

@app.get("/api/inventario/consulta")
async def consulta_inventario(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500),
    busqueda: Optional[str] = Query(None),
    categoria: Optional[str] = Query(None),
    responsable: Optional[str] = Query(None)
):
    """Consulta paginada del inventario"""
    try:
        # Obtener todos los artículos
        todos_articulos = get_google_sheet_data()
        
        # Aplicar filtros
        articulos_filtrados = todos_articulos
        
        if busqueda:
            busqueda = busqueda.lower()
            articulos_filtrados = [
                art for art in articulos_filtrados 
                if busqueda in art.get('nombre', '').lower() or 
                   busqueda in art.get('placa', '').lower() or
                   busqueda in art.get('descripcion', '').lower()
            ]
        
        if categoria:
            articulos_filtrados = [
                art for art in articulos_filtrados 
                if categoria.lower() in art.get('categoria', '').lower()
            ]
        
        if responsable:
            articulos_filtrados = [
                art for art in articulos_filtrados 
                if responsable.lower() in art.get('responsable', '').lower()
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
            "total_pages": (total + limit - 1) // limit
        }
        
    except Exception as e:
        return {"error": str(e), "articulos": [], "total": 0}

@app.get("/api/inventario/estadisticas")
async def get_estadisticas():
    """Estadísticas del inventario"""
    try:
        articulos = get_google_sheet_data()
        
        if not articulos:
            return {"error": "No hay datos disponibles"}
        
        # Calcular estadísticas
        total_articulos = len(articulos)
        valor_total = sum(float(art.get('valor', 0)) for art in articulos)
        
        # Top categorías
        categorias = {}
        for art in articulos:
            cat = art.get('categoria', 'Sin categoría')
            categorias[cat] = categorias.get(cat, 0) + 1
        
        top_categorias = [
            {"categoria": cat, "cantidad": cant} 
            for cat, cant in sorted(categorias.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        # Top responsables
        responsables = {}
        for art in articulos:
            resp = art.get('responsable', 'Sin asignar')
            responsables[resp] = responsables.get(resp, 0) + 1
        
        top_responsables = [
            {"responsable": resp, "cantidad": cant}
            for resp, cant in sorted(responsables.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        return {
            "resumen": {
                "total_articulos": total_articulos,
                "valor_total_inventario": valor_total,
                "total_categorias": len(categorias),
                "total_responsables": len(responsables)
            },
            "top_categorias": top_categorias,
            "top_responsables": top_responsables
        }
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/inventario/categorias")
async def get_categorias():
    """Obtener todas las categorías"""
    try:
        articulos = get_google_sheet_data()
        categorias = list(set(art.get('categoria', 'Sin categoría') for art in articulos))
        return sorted(categorias)
    except Exception as e:
        return {"error": str(e), "categorias": []}

@app.get("/api/inventario/responsables") 
async def get_responsables():
    """Obtener todos los responsables"""
    try:
        articulos = get_google_sheet_data()
        responsables = list(set(art.get('responsable', 'Sin asignar') for art in articulos))
        return sorted(responsables)
    except Exception as e:
        return {"error": str(e), "responsables": []}

@app.post("/api/sync/pull")
async def sync_pull():
    """Sincronizar datos desde Google Sheets"""
    try:
        articulos = get_google_sheet_data()
        return {
            "message": "Sincronización exitosa",
            "total_articulos": len(articulos),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}

# Manejo de errores
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
