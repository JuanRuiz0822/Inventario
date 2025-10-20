Write-Host "Iniciando Sistema Inventario SENA..." -ForegroundColor Green
Set-Location backend
if (Test-Path .venv/Scripts/Activate.ps1) {
    .venv/Scripts/Activate.ps1
}
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
