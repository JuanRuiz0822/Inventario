#!/bin/bash

# Ruta del backend y archivo
APP_PY="backend/app.py"
BACKUP="backend/app.py.bak_$(date +%s)"

# Hacer backup seguro
cp "$APP_PY" "$BACKUP"
echo "Backup del app.py creado: $BACKUP"

# Agregar función normalizadora y endpoint robusto, solo si no existe ya
NORMALIZE_FUNC="
def normaliza_placa(p):
    return p.strip().lstrip('0').upper()
"

ENDPOINT_FUNC="
@app.get(\"/api/inventario/{placa}/detalle\")
async def detalle_articulo(placa: str):
    articulos = get_google_sheet_data()
    placa_norm = normaliza_placa(placa)
    for art in articulos:
        if normaliza_placa(art['placa']) == placa_norm:
            return {\"articulo\": art}
    raise HTTPException(404, \"Artículo no encontrado\")
"

# Inserta la función normalizadora si no está
grep -q "def normaliza_placa" "$APP_PY" || \
    sed -i "/^_cache = None/i $NORMALIZE_FUNC" "$APP_PY"

# Elimina cualquier endpoint previo para detalle para evitar duplicidad
sed -i "/@app.get(\"\/api\/inventario\/{placa}\/detalle\")/,/^$/d" "$APP_PY"

# Inserta el endpoint corregido al final del archivo
echo "$ENDPOINT_FUNC" >> "$APP_PY"

echo "Ajuste realizado. El endpoint de detalle ahora es robusto."
echo "Reinicia tu backend con:"
echo "    python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000"
