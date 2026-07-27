param(
  [switch]$OverwriteEnv,
  [switch]$RestoreState
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

if ($RestoreState.IsPresent) {
  & (Join-Path $PSScriptRoot "restore-server-state.ps1") -Force
}

& (Join-Path $PSScriptRoot "setup-local-env.ps1") -Overwrite:$OverwriteEnv

function Ensure-Venv([string]$AppRoot, [string[]]$RequirementFiles) {
  Push-Location $AppRoot
  try {
    if (-not (Test-Path ".venv\Scripts\python.exe")) {
      python -m venv .venv
    }
    $python = (Resolve-Path ".venv\Scripts\python.exe").Path
    & $python -m pip install --upgrade pip setuptools wheel
    foreach ($req in $RequirementFiles) {
      & $python -m pip install -r $req
    }
  } finally {
    Pop-Location
  }
}

Ensure-Venv -AppRoot (Join-Path $root "apps\auth-portal") -RequirementFiles @("requirements.txt")
Ensure-Venv -AppRoot (Join-Path $root "apps\multiagent") -RequirementFiles @("requirements.txt", "local_web_portal\requirements.txt")
Ensure-Venv -AppRoot (Join-Path $root "apps\novelclaw") -RequirementFiles @("requirements.txt", "local_web_portal\requirements.txt")

Write-Host ""
Write-Host "Bootstrap finished."
Write-Host "Next step:"
Write-Host "  .\scripts\start-all-local.ps1"
