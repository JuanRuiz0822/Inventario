Write-Host "== Iniciando corrección de rutas =="

# Definir rutas frontend y backend
$frontend = "C:\Users\Sennova\Desktop\prototipo_inventario_local\frontend"
$backend = "C:\Users\Sennova\Desktop\prototipo_inventario_local\backend"

# Crear carpetas si no existen
if (-not (Test-Path $frontend)) { New-Item -Path $frontend -ItemType Directory }
if (-not (Test-Path $backend)) { New-Item -Path $backend -ItemType Directory }

# Mover frontend (HTML)
Move-Item -Path ".\admin.html" -Destination $frontend -Force

# Mover backend (app y base de datos)
Move-Item -Path ".\app.py" -Destination $backend -Force
Move-Item -Path ".\inventario.db" -Destination $backend -Force
Move-Item -Path ".\requirements.txt" -Destination $backend -Force

# Mensaje final
Write-Host "Archivos movidos correctamente."

Write-Host "== Limpiando archivos duplicados =="

# Lista de archivos que ya movimos
$archivosMovidos = @("admin.html", "app.py", "inventario.db", "requirements.txt")

foreach ($archivo in $archivosMovidos) {
    $ruta = "C:\Users\Sennova\Desktop\prototipo_inventario_local\prototipo_inventario\$archivo"
    if (Test-Path $ruta) {
        Remove-Item $ruta -Force
        Write-Host "Eliminado duplicado: $archivo"
    }
}

Write-Host "✅ Limpieza finalizada. El sistema está organizado en frontend y backend."
