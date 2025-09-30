#!/usr/bin/env bash
set -e

BACKEND="backend/app.py"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "🔧 Realizando backup de $BACKEND..."
cp "$BACKEND" "${BACKEND}.backup_${TIMESTAMP}"
echo "✅ Backup creado: ${BACKEND}.backup_${TIMESTAMP}"

echo "📄 Agregando endpoints de inventario a $BACKEND..."

cat << 'EOF' >> "$BACKEND"

# ===== Endpoints AGREGADOS: Inventario =====

@app.get("/api/inventario/consulta")
async def consulta_inventario(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500)
):
    """Consulta paginada del inventario"""
    articulos = get_google_sheet_data()
    total = len(articulos)
    start = (page - 1) * limit
    return {
        "articulos": articulos[start:start+limit],
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit
    }

@app.get("/api/inventario/categorias")
async def get_categorias():
    """Obtener categorías únicas"""
    articulos = get_google_sheet_data()
    categorias = sorted({art.get("categoria","") for art in articulos})
    return categorias

@app.get("/api/inventario/responsables")
async def get_responsables():
    """Obtener responsables únicos"""
    articulos = get_google_sheet_data()
    responsables = sorted({art.get("responsable","") for art in articulos})
    return responsables

@app.get("/api/inventario/estadisticas")
async def get_estadisticas():
    """Estadísticas del inventario"""
    articulos = get_google_sheet_data()
    return {
        "total_articulos": len(articulos),
        "hojas_procesadas": len({art.get("hoja") for art in articulos})
    }
EOF

echo "✅ Endpoints agregados. Reinicia el servidor:"
echo "   cd backend && uvicorn app:app --reload --host 0.0.0.0 --port 8000"
