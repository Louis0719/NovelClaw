param(
  [switch]$EnsureEnv,
  [switch]$RestoreState,
  [switch]$RestartExisting,
  [switch]$UseSharedVenv
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

if ($RestoreState.IsPresent) {
  & (Join-Path $PSScriptRoot "restore-server-state.ps1") -Force
}

if ($EnsureEnv.IsPresent) {
  & (Join-Path $PSScriptRoot "bootstrap-local.ps1")
} else {
  & (Join-Path $PSScriptRoot "setup-local-env.ps1")
}

function Get-ListeningProcessInfo {
  param(
    [int]$Port
  )
  $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
  if (-not $conn) {
    return $null
  }
  $proc = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
  [pscustomobject]@{
    Port = $Port
    ProcessId = $conn.OwningProcess
    ProcessName = if ($proc) { $proc.ProcessName } else { "" }
    Path = if ($proc) { $proc.Path } else { "" }
  }
}

function Ensure-CoreModules {
  param(
    [string]$PythonExe,
    [string]$Workdir,
    [string[]]$RequirementFiles
  )

  $installed = (& $PythonExe -m pip list --format=freeze 2>$null | Out-String)
  if (
    $installed -match "(?m)^uvicorn==" -and
    $installed -match "(?m)^fastapi==" -and
    $installed -match "(?m)^sqlalchemy=="
  ) {
    return
  }

  Write-Host "[fix] missing local modules in $Workdir, installing requirements..."
  Push-Location $Workdir
  try {
    & $PythonExe -m pip install --upgrade pip setuptools wheel
    foreach ($req in $RequirementFiles) {
      & $PythonExe -m pip install -r $req
    }
  } finally {
    Pop-Location
  }
}

$sharedPython = Join-Path $root ".venv-shared\Scripts\python.exe"

function Resolve-PythonExecutable {
  param(
    [string]$DefaultPython
  )

  if ($UseSharedVenv.IsPresent -or (Test-Path $sharedPython)) {
    if (-not (Test-Path $sharedPython)) {
      throw "Shared venv not found: $sharedPython. Run .\scripts\bootstrap-shared-venv.ps1 first."
    }
    return $sharedPython
  }

  return $DefaultPython
}

$services = @(
  @{
    Name = "CoLong Auth Portal :8010"
    Workdir = Join-Path $root "apps\auth-portal"
    Python = Join-Path $root "apps\auth-portal\.venv\Scripts\python.exe"
    Port = 8010
    RequirementFiles = @("requirements.txt")
    Args = "-m uvicorn local_web_portal.app.main:app --host 127.0.0.1 --port 8010"
  },
  @{
    Name = "CoLong MultiAgent :8011"
    Workdir = Join-Path $root "apps\multiagent"
    Python = Join-Path $root "apps\multiagent\.venv\Scripts\python.exe"
    Port = 8011
    RequirementFiles = @("requirements.txt", "local_web_portal\requirements.txt")
    Args = "-m uvicorn local_web_portal.app.main:app --host 127.0.0.1 --port 8011"
  },
  @{
    Name = "NovelClaw Workspace :8012"
    Workdir = Join-Path $root "apps\novelclaw"
    Python = Join-Path $root "apps\novelclaw\.venv\Scripts\python.exe"
    Port = 8012
    RequirementFiles = @("requirements.txt", "local_web_portal\requirements.txt")
    Args = "-m uvicorn local_web_portal.app.main:app --host 127.0.0.1 --port 8012"
  }
)

foreach ($svc in $services) {
  $pythonExe = Resolve-PythonExecutable -DefaultPython $svc.Python

  if (-not (Test-Path $pythonExe)) {
    throw "Missing venv for $($svc.Name): $pythonExe. Run .\scripts\bootstrap-local.ps1 first."
  }

  Ensure-CoreModules -PythonExe $pythonExe -Workdir $svc.Workdir -RequirementFiles $svc.RequirementFiles

  $listener = Get-ListeningProcessInfo -Port $svc.Port
  if ($listener) {
    if ($RestartExisting.IsPresent) {
      try {
        Stop-Process -Id $listener.ProcessId -Force -ErrorAction Stop
        Start-Sleep -Milliseconds 600
        Write-Host "[restarted] closed existing listener on :$($svc.Port) pid=$($listener.ProcessId)"
      } catch {
        throw "Port $($svc.Port) is occupied by pid=$($listener.ProcessId) and could not be stopped."
      }
    } else {
      Write-Host "[reuse] $($svc.Name) already listening on :$($svc.Port) pid=$($listener.ProcessId) $($listener.ProcessName)"
      continue
    }
  }

  $command = "Set-Location '$($svc.Workdir)'; & '$pythonExe' $($svc.Args)"
  Start-Process powershell -WorkingDirectory $svc.Workdir -ArgumentList "-NoExit", "-Command", $command | Out-Null
  Write-Host "[started] $($svc.Name)"
}

Write-Host ""
Write-Host "Open in browser:"
Write-Host "  Auth Portal : http://127.0.0.1:8010/select-mode"
Write-Host "  MultiAgent  : http://127.0.0.1:8011/dashboard"
Write-Host "  NovelClaw   : http://127.0.0.1:8012/dashboard"
