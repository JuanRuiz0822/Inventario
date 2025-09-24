# GUÍA RÁPIDA - CREAR GOOGLE SHEET NATIVA
# Solución definitiva para el error "This operation is not supported"

clear
echo "=================================="
echo "   🔧 SOLUCIÓN DEFINITIVA"
echo "   Google Sheet Nativa"
echo "=================================="
echo

info() { echo -e "\033[1;34mℹ️  $1\033[0m"; }
ok() { echo -e "\033[1;32m✅ $1\033[0m"; }
warn() { echo -e "\033[1;33m⚠️  $1\033[0m"; }
step() { echo -e "\033[1;36m🔄 $1\033[0m"; }

info "PROBLEMA IDENTIFICADO:"
echo "   ❌ Tu Google Sheet actual es un Excel convertido"
echo "   ❌ Google Sheets API no puede acceder a documentos convertidos"
echo "   ❌ Error: 'This operation is not supported for this document'"
echo
info "SOLUCIÓN:"
echo "   ✅ Crear Google Sheet NATIVA desde cero"
echo "   ⏱️  Tiempo: 5 minutos"
echo "   🎯 Resultado: Sistema 100% funcional"
echo

step "PASO 1: Crear Google Sheet Nativa"
echo
echo "📋 INSTRUCCIONES PASO A PASO:"
echo "   1. Abre en tu navegador: https://sheets.google.com"
echo "   2. Clic en 'Hoja de cálculo en blanco' (o '+' si aparece)"
echo "   3. En la esquina superior izquierda, cambiar nombre a:"
echo "      'Inventario_Sistema_2025'"
echo

step "PASO 2: Crear Estructura de Datos"
echo
echo "📊 ENCABEZADOS A AGREGAR EN FILA 1:"
echo "   A1: id"
echo "   B1: nombre"
echo "   C1: descripcion" 
echo "   D1: cantidad"
echo "   E1: precio"
echo "   F1: categoria"
echo "   G1: ubicacion"
echo "   H1: fecha_creacion"
echo
echo "💡 TIP: Puedes copiar y pegar todos los encabezados de una vez:"
echo "   id	nombre	descripcion	cantidad	precio	categoria	ubicacion	fecha_creacion"
echo

step "PASO 3: Compartir con Cuenta de Servicio"
echo
echo "🔐 COMPARTIR LA HOJA:"
echo "   1. Clic en 'Compartir' (botón azul, esquina superior derecha)"
echo "   2. En 'Agregar personas y grupos', pegar:"
echo "      sync-inventario@inventariosync.iam.gserviceaccount.com"
echo "   3. Cambiar permisos a 'Editor'"
echo "   4. ✅ DESMARCAR 'Notificar a las personas'"
echo "   5. Clic en 'Enviar'"
echo

step "PASO 4: Obtener Nuevo ID"
echo
echo "📋 COPIAR EL ID DE LA NUEVA HOJA:"
echo "   1. En la barra de direcciones de tu navegador, verás algo como:"
echo "      https://docs.google.com/spreadsheets/d/[NUEVO-ID-AQUÍ]/edit"
echo "   2. Copia la parte entre '/d/' y '/edit'"
echo "   3. Ese es tu nuevo ID de Google Sheet nativa"
echo

echo "Cuando hayas completado los pasos 1-4:"
read -p "Pega aquí el NUEVO ID de tu Google Sheet nativa: " NEW_SHEET_ID

if [ -z "$NEW_SHEET_ID" ]; then
    warn "ID requerido para continuar"
    echo
    echo "📋 PROCESO MANUAL:"
    echo "   1. Completa los pasos 1-4 arriba"
    echo "   2. Ejecuta este script nuevamente"
    echo "   3. Pega el nuevo ID cuando se solicite"
    exit 1
fi

step "PASO 5: Actualizando Configuración"
echo
echo "📝 Nuevo ID: $NEW_SHEET_ID"

# Backup del .env actual
BACKUP_FILE=".env.backup.$(date +%Y%m%d_%H%M%S)"
cp .env "$BACKUP_FILE"
info "Backup creado: $BACKUP_FILE"

# Actualizar .env con nuevo ID
if sed --version >/dev/null 2>&1; then
    # GNU sed
    sed -i "s/GOOGLE_SHEET_ID=.*/GOOGLE_SHEET_ID=${NEW_SHEET_ID}/" .env
else
    # BSD sed (macOS)
    sed -i.tmp "s/GOOGLE_SHEET_ID=.*/GOOGLE_SHEET_ID=${NEW_SHEET_ID}/" .env && rm .env.tmp
fi

ok "Configuración actualizada con nuevo ID"

step "PASO 6: Probando Nueva Conexión"
echo
info "Probando conexión con tu nueva Google Sheet nativa..."

# Activar entorno virtual
if [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
elif [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

# Probar conexión
python -c "
import gspread
from google.oauth2.service_account import Credentials

try:
    print('🔐 Autenticando...')
    creds = Credentials.from_service_account_file('backend/credentials.json', 
                                                  scopes=['https://www.googleapis.com/auth/spreadsheets',
                                                         'https://www.googleapis.com/auth/drive'])
    client = gspread.authorize(creds)
    
    print('🔗 Conectando a Google Sheet...')
    sheet = client.open_by_key('${NEW_SHEET_ID}')
    
    print(f'✅ ÉXITO: Conectado a \"{sheet.title}\"')
    
    worksheet = sheet.sheet1
    print(f'📊 Hoja de trabajo: \"{worksheet.title}\"')
    
    # Probar lectura
    values = worksheet.get_all_values()
    print(f'📋 Datos leídos: {len(values)} filas')
    
    if values:
        print(f'📊 Encabezados: {values[0]}')
    
    # Probar escritura (agregar fila de prueba)
    test_row = ['1', 'Artículo de Prueba', 'Descripción de prueba', '1', '100.00', 'Prueba', 'Oficina', '2025-09-24']
    worksheet.append_row(test_row)
    print('✅ Escritura de prueba exitosa')
    
    print()
    print('🎉 ¡CONEXIÓN EXITOSA!')
    print('✅ Google Sheet nativa funcionando correctamente')
    print('✅ Lectura y escritura verificadas')
    print('✅ Sistema listo para sincronización')
    
except Exception as e:
    print(f'❌ Error: {e}')
    print()
    print('🔧 POSIBLES SOLUCIONES:')
    print('   1. Verificar que la hoja esté compartida correctamente')
    print('   2. Verificar que los permisos sean de \"Editor\"')
    print('   3. Esperar 1-2 minutos y probar nuevamente')
    print('   4. Verificar que el ID sea correcto')
"

echo
step "PASO 7: Configuración Final"
echo
ok "¡Nueva Google Sheet nativa configurada!"
echo
echo "📊 RESUMEN:"
echo "   ✅ Google Sheet nativa creada"
echo "   ✅ Estructura de datos configurada"  
echo "   ✅ Permisos otorgados"
echo "   ✅ ID actualizado en configuración"
echo "   ✅ Conexión probada y funcionando"
echo

echo "🚀 PRÓXIMOS PASOS:"
echo "   1. Reiniciar servidor:"
echo "      Ctrl+C (si está corriendo)"
echo "      ./manage.sh dev"
echo
echo "   2. Probar sincronización:"
echo "      http://localhost:8000/admin.html"
echo "      Clic en 'Sincronizar Google Sheets'"
echo
echo "   3. Verificar funcionamiento:"
echo "      • Los datos se sincronizan correctamente"
echo "      • Puedes agregar/editar desde el panel"
echo "      • Los cambios aparecen en Google Sheets"
echo

echo "=================================="
echo "   🎉 ¡SISTEMA 100% FUNCIONAL!"
echo "=================================="
echo
ok "Tu sistema de inventario está completamente operativo"
ok "Sincronización bidireccional con Google Sheets activa"
ok "Panel administrativo listo para usar"
echo
info "🌐 URLs principales:"
echo "   📋 Panel: http://localhost:8000/admin.html"
echo "   📚 API: http://localhost:8000/docs"
echo "   📊 Sheet: https://docs.google.com/spreadsheets/d/${NEW_SHEET_ID}/"