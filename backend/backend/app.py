from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

# Crear la aplicación FastAPI
app = FastAPI(title="Sistema de Inventario")

# Montar la carpeta 'static' para servir archivos HTML y otros estáticos
# La carpeta 'static' está al mismo nivel que app.py
app.mount("/", StaticFiles(directory="static", html=True), name="static")

# Ruta de prueba opcional
@app.get("/ping")
async def ping():
    return {"message": "Pong"}
