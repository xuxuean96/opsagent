$ErrorActionPreference = "Stop"

if (-not (Test-Path "config/app.yaml")) {
  Copy-Item "config/app.yaml.example" "config/app.yaml"
}

python -m ops_agent.cli index
python -m uvicorn ops_agent.app:app --host 0.0.0.0 --port 8000
