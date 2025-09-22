from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import sqlite3
import os

# Inicializar FastAPI
app = FastAPI(title="Sistema de Inventario")

# Permitir CORS (para que el frontend pueda hacer peticiones al backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # en producción reemplazar con el dominio real
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ======================
#   CONFIG BASE DE DATOS
# ======================
DB_PATH = os.path.join(os.path.dirname(__file__), "inventario.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Para devolver resultados como diccionario
    return conn

# ======================
#   ENDPOINTS API
# ======================

@app.get("/api/articulos")
def obtener_articulos():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM articulos LIMIT 100")
        articulos = cursor.fetchall()
        conn.close()

        return [dict(row) for row in articulos]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/articulos/{id}")
def obtener_articulo(id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM articulos WHERE id = ?", (id,))
        articulo = cursor.fetchone()
        conn.close()

        if articulo is None:
            raise HTTPException(status_code=404, detail="Artículo no encontrado")

        return dict(articulo)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/articulos")
def agregar_articulo(nombre: str, cantidad: int, precio: float):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO articulos (nombre, cantidad, precio) VALUES (?, ?, ?)",
            (nombre, cantidad, precio),
        )
        conn.commit()
        nuevo_id = cursor.lastrowid
        conn.close()

        return JSONResponse(
            content={"message": "Artículo agregado correctamente", "id": nuevo_id},
            status_code=201,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/articulos/{id}")
def actualizar_articulo(id: int, nombre: str, cantidad: int, precio: float):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE articulos SET nombre=?, cantidad=?, precio=? WHERE id=?",
            (nombre, cantidad, precio, id),
        )
        conn.commit()
        cambios = cursor.rowcount
        conn.close()

        if cambios == 0:
            raise HTTPException(status_code=404, detail="Artículo no encontrado")

        return {"message": "Artículo actualizado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/articulos/{id}")
def eliminar_articulo(id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM articulos WHERE id=?", (id,))
        conn.commit()
        cambios = cursor.rowcount
        conn.close()

        if cambios == 0:
            raise HTTPException(status_code=404, detail="Artículo no encontrado")

        return {"message": "Artículo eliminado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ======================
#   SERVIR FRONTEND
# ======================
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")

sed -i "/from fastapi import FastAPI/i from fastapi import BackgroundTasks\nimport sync_gs" backend/app.py

cat >> backend/app.py << 'EOF'

# Endpoints para sincronización con Google Sheets
@app.post("/api/sync/pull")
def api_sync_pull(background_tasks: BackgroundTasks):
    background_tasks.add_task(sync_gs.pull_sheet_to_sqlite)
    return {"started": True, "action": "pull"}

@app.post("/api/sync/push")
def api_sync_push(background_tasks: BackgroundTasks):
    background_tasks.add_task(sync_gs.push_sqlite_to_sheet)
    return {"started": True, "action": "push"}
EOF
