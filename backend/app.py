from fastapi import FastAPI, HTTPException, BackgroundTasks
import sqlite3
import os
from fastapi.middleware.cors import CORSMiddleware
import sync_gs
from fastapi.staticfiles import StaticFiles
from typing import Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoints para sincronización con Google Sheets
@app.post("/api/sync/pull")
def api_sync_pull(background_tasks: BackgroundTasks):
    background_tasks.add_task(sync_gs.pull_sheet_to_sqlite)
    return {"started": True, "action": "pull"}

@app.post("/api/sync/push")
def api_sync_push(background_tasks: BackgroundTasks):
    background_tasks.add_task(sync_gs.push_sqlite_to_sheet)
    return {"started": True, "action": "push"}

# Servir frontend estático
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/frontend", StaticFiles(directory=frontend_path), name="frontend")

# Endpoint de prueba para artículos
@app.get("/api/articulos")
def get_articulos(q: Optional[str] = None):
    db_path = os.path.join(os.path.dirname(__file__), "inventario.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if q:
        cursor.execute("SELECT * FROM articulos WHERE nombre LIKE ?", ('%'+q+'%',))
    else:
        cursor.execute("SELECT * FROM articulos")
    
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows
