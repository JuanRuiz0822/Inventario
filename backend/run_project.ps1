cat > backend/run_project.ps1 << 'EOF'
cd (Split-Path -Parent $MyInvocation.MyCommand.Definition)
if (-Not (Test-Path ".venv")) {
    python -m venv .venv
}
. .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
uvicorn app:app --reload --host 0.0.0.0 --port 8000
EOF
