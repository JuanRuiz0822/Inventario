#!/bin/bash

# CONFIGURACIÓN AUTOMÁTICA GOOGLE SHEETS
# Para el usuario con ID específico: 1E68HmwdDy8TuP3FH9KCJbv6TnZ6-tj0i

echo "🔧 CONFIGURANDO GOOGLE SHEETS AUTOMÁTICAMENTE..."

# Función para verificar archivos
check_file() {
    if [ -f "$1" ]; then
        echo "✅ $1 - Existe"
        return 0
    else
        echo "❌ $1 - No existe"
        return 1
    fi
}

# PASO 1: Verificar/copiar credentials.json
echo "📁 PASO 1: Configurando credentials.json..."
if [ ! -f "backend/credentials.json" ]; then
    echo "⚠️  Buscando archivo en Descargas..."
    CRED_FILE=$(find ~/Downloads -name "*inventariosync*.json" -o -name "*credentials*.json" 2>/dev/null | head -1)

    if [ -n "$CRED_FILE" ]; then
        cp "$CRED_FILE" backend/credentials.json
        echo "✅ Archivo copiado: $CRED_FILE → backend/credentials.json"
    else
        echo "❌ No se encontró credentials.json en Descargas"
        echo "📋 ACCIÓN MANUAL REQUERIDA:"
        echo "   1. Descarga credentials.json de Google Cloud Console"
        echo "   2. Cópialo a: backend/credentials.json"
        exit 1
    fi
else
    echo "✅ credentials.json ya existe"
fi

# PASO 2: Configurar variables de entorno
echo "⚙️  PASO 2: Configurando variables de entorno..."
cat > .env << 'EOF'
# Configuración del Sistema de Inventario
DATABASE_URL=sqlite:///backend/inventario.db
HOST=127.0.0.1
PORT=8000
DEBUG=true

# Google Sheets Configuration - TU CONFIGURACIÓN ESPECÍFICA
GOOGLE_CREDENTIALS_FILE=backend/credentials.json
GOOGLE_SHEET_ID=1E68HmwdDy8TuP3FH9KCJbv6TnZ6-tj0i
GOOGLE_SHEET_NAME=Sheet1
EOF
echo "✅ Variables de entorno configuradas"

# PASO 3: Probar conexión
echo "🧪 PASO 3: Probando conexión..."
python -c "
import sys, os
sys.path.append('backend')
try:
    import gspread
    from google.oauth2.service_account import Credentials

    creds = Credentials.from_service_account_file('backend/credentials.json', 
                                                  scopes=['https://www.googleapis.com/auth/spreadsheets'])
    client = gspread.authorize(creds)
    sheet = client.open_by_key('1E68HmwdDy8TuP3FH9KCJbv6TnZ6-tj0i')
    print(f'✅ Conexión exitosa con: {sheet.title}')
except Exception as e:
    print(f'❌ Error de conexión: {e}')
    print('🔧 Verificar que la hoja esté compartida')
"

echo "🎉 CONFIGURACIÓN COMPLETADA"
echo "📋 PRÓXIMOS PASOS:"
echo "   1. Compartir Google Sheet con: sync-inventario@inventariosync.iam.gserviceaccount.com"
echo "   2. Reiniciar servidor: ./manage.sh dev"
echo "   3. Probar en: http://localhost:8000/admin.html"
