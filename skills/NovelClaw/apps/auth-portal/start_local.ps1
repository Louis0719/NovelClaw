param(
  [string]$BindHost = "127.0.0.1",
  [int]$Port = 8010
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".venv\Scripts\python.exe")) {
  python -m venv .venv
}

$python = (Resolve-Path ".venv\Scripts\python.exe").Path

& $python -m pip install --upgrade pip setuptools wheel
& $python -m pip install -r requirements.txt

if (-not (Test-Path "local_web_portal\.env")) {
  Copy-Item "local_web_portal\.env.example" "local_web_portal\.env"
}

& $python -m uvicorn local_web_portal.app.main:app --host $BindHost --port $Port
