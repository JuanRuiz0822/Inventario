
# app.py - FastAPI scaffold (archivo generado por crear_prototipo.py)
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
import sqlite3, os
from typing import Optional

DB = os.path.join(os.path.dirname(__file__), "inventario.db")

def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

app = FastAPI(title="Inventario - Prototipo Local")
app.mount("/", StaticFiles(directory=os.path.dirname(__file__), html=True), name="static")

@app.get("/api/articulos")
def listar_articulos(q: Optional[str] = None, limit: int = 200):
    conn = get_conn(); cur = conn.cursor()
    if q:
        cur.execute("SELECT * FROM articulos WHERE 1=1 AND (descripcion LIKE ? OR 1=1)", (f'%{q}%',))
    else:
        cur.execute("SELECT * FROM articulos")
    rows = [dict(r) for r in cur.fetchmany(limit)]
    conn.close()
    return rows

@app.get("/api/ubicaciones")
def listar_ubicaciones():
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM ubicaciones")
        rows = [dict(r) for r in cur.fetchall()]
    except Exception:
        rows = []
    conn.close()
    return rows
