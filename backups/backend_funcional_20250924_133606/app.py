from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import sqlite3
import os
from fastapi.middleware.cors import CORSMiddleware
import sync_gs
from fastapi.staticfiles import StaticFiles
from typing import Optional

app = FastAPI(
    title="Sistema de Inventario API",
    description="API optimizada para gestión de inventario con integración Google Sheets",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurar rutas de archivos estáticos
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/frontend", StaticFiles(directory=frontend_path), name="frontend")

# Ruta directa para admin.html (SOLUCIÓN AL PROBLEMA)
@app.get("/admin.html")
async def get_admin():
    """Servir el panel administrativo"""
    admin_file = os.path.join(os.path.dirname(__file__), "..", "frontend", "admin.html")
    if os.path.exists(admin_file):
        return FileResponse(admin_file)
    else:
        raise HTTPException(status_code=404, detail="Admin panel not found")

# Ruta raíz que redirecciona al admin
@app.get("/")
async def root():
    """Ruta raíz que redirecciona al panel administrativo"""
    return {"message": "Sistema de Inventario API v3.0", "admin_panel": "/admin.html", "docs": "/docs"}

# Endpoints para sincronización con Google Sheets
@app.post("/api/sync/pull")
def api_sync_pull(background_tasks: BackgroundTasks):
    """Importar datos desde Google Sheets"""
    try:
        background_tasks.add_task(sync_gs.pull_sheet_to_sqlite)
        return {"started": True, "action": "pull", "message": "Importación iniciada"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en sync pull: {str(e)}")

@app.post("/api/sync/push")  
def api_sync_push(background_tasks: BackgroundTasks):
    """Exportar datos a Google Sheets"""
    try:
        background_tasks.add_task(sync_gs.push_sqlite_to_sheet)
        return {"started": True, "action": "push", "message": "Exportación iniciada"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en sync push: {str(e)}")

# Endpoint principal de artículos
@app.get("/api/articulos")
def get_articulos(q: Optional[str] = None):
    """Obtener todos los artículos del inventario"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), "inventario.db")
        
        # Crear base de datos si no existe
        if not os.path.exists(db_path):
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articulos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    descripcion TEXT,
                    cantidad INTEGER DEFAULT 0,
                    precio REAL DEFAULT 0.0,
                    categoria TEXT,
                    ubicacion TEXT,
                    fecha_creacion DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Insertar datos de ejemplo
            cursor.execute('''
                INSERT INTO articulos (nombre, descripcion, cantidad, precio, categoria, ubicacion)
                VALUES 
                ('Laptop Dell', 'Laptop Dell Inspiron 15', 5, 899.99, 'Tecnología', 'Oficina A'),
                ('Mouse Inalambrico', 'Mouse óptico inalámbrico', 25, 29.99, 'Accesorios', 'Almacén B'),
                ('Monitor 24"', 'Monitor LED 24 pulgadas', 8, 199.99, 'Tecnología', 'Oficina A')
            ''')
            conn.commit()
            conn.close()
            
            # Reconectar para consulta
            conn = sqlite3.connect(db_path)
        else:
            conn = sqlite3.connect(db_path)
            
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if q:
            cursor.execute("SELECT * FROM articulos WHERE nombre LIKE ? OR descripcion LIKE ?", 
                         ('%'+q+'%', '%'+q+'%'))
        else:
            cursor.execute("SELECT * FROM articulos")
            
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        
        return {
            "total": len(rows),
            "articulos": rows,
            "message": f"Se encontraron {len(rows)} artículos"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener artículos: {str(e)}")

# Endpoint para obtener estadísticas
@app.get("/api/stats")
def get_stats():
    """Obtener estadísticas del inventario"""
    try:
        db_path = os.path.join(os.path.dirname(__file__), "inventario.db")
        if not os.path.exists(db_path):
            return {"total_articulos": 0, "total_valor": 0, "categorias": 0}
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Total de artículos
        cursor.execute("SELECT COUNT(*) as total FROM articulos")
        total_articulos = cursor.fetchone()[0]
        
        # Valor total del inventario
        cursor.execute("SELECT SUM(cantidad * precio) as total_valor FROM articulos")
        total_valor = cursor.fetchone()[0] or 0
        
        # Categorías únicas
        cursor.execute("SELECT COUNT(DISTINCT categoria) as categorias FROM articulos")
        categorias = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_articulos": total_articulos,
            "total_valor": round(total_valor, 2),
            "categorias": categorias,
            "status": "ok"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener estadísticas: {str(e)}")

# Health check endpoint
@app.get("/health")
def health_check():
    """Verificar estado del sistema"""
    return {
        "status": "healthy",
        "version": "3.0.0",
        "database": "connected" if os.path.exists(os.path.join(os.path.dirname(__file__), "inventario.db")) else "not_found",
        "message": "Sistema funcionando correctamente"
    }
