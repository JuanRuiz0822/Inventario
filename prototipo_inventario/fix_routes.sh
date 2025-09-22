#!/bin/bash
# Script para ajustar rutas del backend FastAPI a /api/*

# Ruta del archivo principal (ajústala si tu app no se llama app.py)
APP_FILE="app.py"

echo "🔎 Revisando archivo $APP_FILE ..."

# Reemplazar /articulos por /api/articulos
sed -i 's|@app.get("/articulos"|@app.get("/api/articulos"|g' $APP_FILE
sed -i 's|@app.post("/articulos"|@app.post("/api/articulos"|g' $APP_FILE
sed -i 's|@app.put("/articulos"|@app.put("/api/articulos"|g' $APP_FILE
sed -i 's|@app.delete("/articulos"|@app.delete("/api/articulos"|g' $APP_FILE

# Reemplazar /ubicaciones por /api/ubicaciones
sed -i 's|@app.get("/ubicaciones"|@app.get("/api/ubicaciones"|g' $APP_FILE
sed -i 's|@app.post("/ubicaciones"|@app.post("/api/ubicaciones"|g' $APP_FILE
sed -i 's|@app.put("/ubicaciones"|@app.put("/api/ubicaciones"|g' $APP_FILE
sed -i 's|@app.delete("/ubicaciones"|@app.delete("/api/ubicaciones"|g' $APP_FILE

echo "✅ Rutas actualizadas en $APP_FILE"

# Reiniciar el servidor
echo "🚀 Iniciando FastAPI en http://0.0.0.0:8000 ..."
uvicorn app:app --reload --host 0.0.0.0 --port 8000
