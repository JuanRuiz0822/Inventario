#!/bin/bash

VENV=".venv"
BACKEND="backend"

info() { echo "ℹ️  $1"; }
ok() { echo "✅ $1"; }
err() { echo "❌ $1"; }

activate_venv() {
    if [ -f "$VENV/Scripts/activate" ]; then
        source $VENV/Scripts/activate
        info "Entorno virtual activado"
    elif [ -f "$VENV/bin/activate" ]; then
        source $VENV/bin/activate
        info "Entorno virtual activado"
    else
        err "Entorno virtual no encontrado"
        exit 1
    fi
}

case "${1:-help}" in
    dev)
        info "🚀 Iniciando servidor de desarrollo..."
        activate_venv
        cd $BACKEND
        echo
        echo "🌐 URLs disponibles:"
        echo "  - Panel Admin: http://localhost:8000/admin.html"
        echo "  - API Docs: http://localhost:8000/docs" 
        echo "  - API Artículos: http://localhost:8000/api/articulos"
        echo
        echo "💡 Presiona Ctrl+C para detener"
        echo
        uvicorn app:app --reload --host 127.0.0.1 --port 8000
        ;;
    
    status)
        info "📊 Estado del proyecto:"
        [ -d "$VENV" ] && echo "   ✅ Entorno virtual" || echo "   ❌ Sin entorno"
        [ -f "$BACKEND/app.py" ] && echo "   ✅ Backend" || echo "   ❌ Sin backend"
        [ -f "frontend/admin.html" ] && echo "   ✅ Frontend" || echo "   ❌ Sin frontend"
        ;;
    
    clean)
        info "🧹 Limpiando..."
        find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find . -name "*.pyc" -delete 2>/dev/null || true
        ok "Limpieza completa"
        ;;
    
    *)
        echo "Sistema de Inventario - Comandos:"
        echo "  dev    - Iniciar desarrollo"
        echo "  status - Ver estado"
        echo "  clean  - Limpiar archivos"
        echo
        echo "Ejemplo: ./manage.sh dev"
        ;;
esac
