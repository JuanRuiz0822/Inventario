#!/bin/bash

VENV=".venv"
BACKEND="backend"

# Función para activar entorno virtual
activate_venv() {
    if [ -f "$VENV/Scripts/activate" ]; then
        source $VENV/Scripts/activate
    elif [ -f "$VENV/bin/activate" ]; then
        source $VENV/bin/activate
    else
        echo "❌ Entorno virtual no encontrado"
        echo "Ejecuta: ./manage.sh setup"
        exit 1
    fi
}

case "${1:-help}" in
    setup)
        echo "🔧 Configurando proyecto..."
        if [ ! -d "$VENV" ]; then
            python -m venv $VENV
            echo "✅ Entorno virtual creado"
        fi
        activate_venv
        pip install --upgrade pip
        pip install -r requirements.txt --upgrade
        mkdir -p data/{uploads,backups,exports} logs tests
        echo "✅ Proyecto configurado"
        echo "Próximo paso: ./manage.sh dev"
        ;;
    
    dev)
        echo "🚀 Iniciando desarrollo..."
        activate_venv
        if [ ! -d "$BACKEND" ]; then
            echo "❌ Directorio backend/ no encontrado"
            exit 1
        fi
        cd $BACKEND
        echo
        echo "🌐 URLs disponibles:"
        echo "  - API Docs: http://localhost:8000/docs"
        echo "  - Admin: http://localhost:8000/admin.html"
        echo "  - ReDoc: http://localhost:8000/redoc"
        echo
        echo "💡 Presiona Ctrl+C para detener"
        echo
        uvicorn app:app --reload --host 127.0.0.1 --port 8000
        ;;
    
    clean)
        echo "🧹 Limpiando archivos temporales..."
        find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
        find . -name "*.pyc" -delete 2>/dev/null || true
        find . -name "*.log" -delete 2>/dev/null || true
        echo "✅ Limpieza completada"
        ;;
    
    status)
        echo "📊 Estado del proyecto:"
        echo
        [ -d "$VENV" ] && echo "   ✅ Entorno virtual: Existe" || echo "   ❌ Entorno virtual: No existe"
        [ -f "$BACKEND/inventario.db" ] && echo "   ✅ Base de datos: Existe" || echo "   ⚠️  Base de datos: Se creará al iniciar"
        [ -d "config" ] && echo "   ✅ Configuración: Existe" || echo "   ❌ Configuración: No existe"
        [ -d "data" ] && echo "   ✅ Directorio datos: Existe" || echo "   ❌ Directorio datos: No existe"
        ;;
    
    backup)
        echo "💾 Creando backup..."
        mkdir -p data/backups
        BACKUP_FILE="backup_$(date +%Y%m%d_%H%M%S).db"
        if [ -f "$BACKEND/inventario.db" ]; then
            cp "$BACKEND/inventario.db" "data/backups/$BACKUP_FILE"
            echo "✅ Backup creado: data/backups/$BACKUP_FILE"
        else
            echo "⚠️  Base de datos no encontrada"
        fi
        ;;
    
    test)
        echo "🧪 Verificando sistema..."
        activate_venv
        python -c "
import sys
print(f'Python: {sys.version}')
try:
    import fastapi, uvicorn, pandas, gspread
    print('✅ Dependencias principales: OK')
except ImportError as e:
    print(f'⚠️ Error en dependencias: {e}')

import pathlib
if pathlib.Path('config/settings.py').exists():
    print('✅ Configuración: Existe')
if pathlib.Path('backend/app.py').exists():
    print('✅ Backend: Existe')
print('✅ Verificación completada')
"
        ;;
    
    *)
        echo "Sistema de Inventario - Git Bash v3.0"
        echo
        echo "📋 Comandos:"
        echo "  setup  - Configurar proyecto"
        echo "  dev    - Modo desarrollo"
        echo "  clean  - Limpiar archivos"
        echo "  status - Ver estado"
        echo "  backup - Backup BD"  
        echo "  test   - Verificar sistema"
        echo
        echo "Ejemplo: ./manage.sh dev"
        ;;
esac
