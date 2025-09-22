# crear_prototipo.py
# Ejecuta: python crear_prototipo.py
# Pre-requisitos: tener el archivo Excel "Copia de Inventario_2025(1).xlsx" en la misma carpeta.

import os
import sqlite3
import hashlib
import shutil
import json
from pathlib import Path
import pandas as pd

BASE = Path.cwd()
EXCEL = BASE / "Copia de Inventario_2025(1).xlsx"
OUT = BASE / "prototipo_inventario"
OUT.mkdir(exist_ok=True)

DB = OUT / "inventario.db"
CSV_OUT = OUT / "articulos_importados.csv"
ZIP_PATH = BASE / "prototipo_inventario.zip"

if not EXCEL.exists():
    print("ERROR: no encontré el archivo Excel:", EXCEL)
    print("Coloca 'Copia de Inventario_2025(1).xlsx' en esta carpeta y vuelve a ejecutar.")
    raise SystemExit(1)

print("Leyendo Excel...", EXCEL)
xls = pd.read_excel(EXCEL, sheet_name=None)

# Detectar hoja principal (artículos) por nombre
candidates = [name for name in xls.keys() if name.lower().startswith("art") or "artic" in name.lower() or "artículos" in name.lower() or "articulos" in name.lower()]
main_sheet = candidates[0] if candidates else list(xls.keys())[0]
df_art = xls[main_sheet].copy()

# Normalizar nombres de columnas
df_art.columns = [str(c).strip().replace(" ", "_").lower() for c in df_art.columns]

# Crear DB SQLite
if DB.exists():
    DB.unlink()
conn = sqlite3.connect(DB)
cur = conn.cursor()

# Crear tabla articulos (todas TEXT para prototipo)
cols = df_art.columns.tolist()
col_defs = ",\n    ".join([f'"{c}" TEXT' for c in cols])
create_sql = f"""CREATE TABLE articulos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    {col_defs}
);"""
cur.execute(create_sql)

# Crear tabla ubicaciones si existe hoja de ubicaciones
location_sheet_candidates = [name for name in xls.keys() if "ubic" in name.lower() or "ubicaciones" in name.lower()]
if location_sheet_candidates:
    loc_sheet = location_sheet_candidates[0]
    df_loc = xls[loc_sheet].copy()
    df_loc.columns = [str(c).strip().replace(" ", "_").lower() for c in df_loc.columns]
    cur.execute("""CREATE TABLE IF NOT EXISTS ubicaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        detalle TEXT
    );""")
    # insertar nombres únicos
    try:
        loc_names = df_loc.iloc[:,0].astype(str).str.strip().dropna().unique().tolist()
        for ln in loc_names:
            cur.execute("INSERT INTO ubicaciones (nombre, detalle) VALUES (?,?)", (ln, None))
    except Exception:
        pass

# Tabla usuarios (admin)
cur.execute("""CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password_hash TEXT,
    nombre TEXT,
    correo TEXT
);""")
# insertar admin (admin / admin123 -> hash sha256)
def sha256_hash(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()
try:
    cur.execute("INSERT INTO usuarios (username,password_hash,nombre,correo) VALUES (?,?,?,?)",
                ("admin", sha256_hash("admin123"), "Administrador Principal", "admin@local"))
except sqlite3.IntegrityError:
    pass

# Tabla asignaciones
cur.execute("""CREATE TABLE IF NOT EXISTS asignaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    articulo_id INTEGER,
    usuario_id INTEGER,
    fecha_asignacion TEXT,
    ubicacion TEXT
);""")

# Insertar artículos
insert_cols = ",".join([f'"{c}"' for c in cols])
placeholders = ",".join(["?"] * len(cols))
insert_sql = f'INSERT INTO articulos ({insert_cols}) VALUES ({placeholders})'
records = df_art.fillna("").astype(str).values.tolist()
cur.executemany(insert_sql, records)
conn.commit()

# Export CSV
df_art.to_csv(CSV_OUT, index=False)

# Crear app.py (FastAPI) y admin.html simples
app_py = r'''
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
'''

admin_html = r'''
<!doctype html>
<html>
<head><meta charset="utf-8"><title>Inventario - Admin</title></head>
<body>
  <h1>Inventario - Prototipo Admin</h1>
  <div>
    <button onclick="load()">Cargar artículos</button>
    <input id="q" placeholder="buscar..." />
    <button onclick="search()">Buscar</button>
  </div>
  <pre id="list" style="white-space:pre-wrap; border:1px solid #ccc; padding:10px; height:400px; overflow:auto;"></pre>
<script>
async function load(){ 
  const res = await fetch('/api/articulos');
  const data = await res.json();
  document.getElementById('list').innerText = JSON.stringify(data.slice(0,200), null, 2);
}
async function search(){
  const q = document.getElementById('q').value;
  const res = await fetch('/api/articulos?q=' + encodeURIComponent(q));
  const data = await res.json();
  document.getElementById('list').innerText = JSON.stringify(data.slice(0,200), null, 2);
}
</script>
</body>
</html>
'''

req_txt = "fastapi\nuvicorn\npandas\nopenpyxl\n"

# Escribir archivos en OUT
(OUT / "app.py").write_text(app_py, encoding="utf-8")
(OUT / "admin.html").write_text(admin_html, encoding="utf-8")
(OUT / "requirements.txt").write_text(req_txt, encoding="utf-8")
conn.close()

# Crear ZIP
if ZIP_PATH.exists():
    ZIP_PATH.unlink()
shutil.make_archive(str(ZIP_PATH.with_suffix('')), 'zip', root_dir=OUT)
print("Prototipo creado correctamente.")
print("Archivos generados en:", OUT)
print("ZIP generado en:", ZIP_PATH)
print("Instrucciones: abrir la carpeta, crear entorno virtual, pip install -r requirements.txt y ejecutar uvicorn app:app --reload --host 0.0.0.0 --port 8000")
