$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$venv = Join-Path $root ".venv-shared"

function Resolve-BootstrapPython {
  $candidates = @(
    @{ Name = "py"; Args = @("-3") },
    @{ Name = "python"; Args = @() },
    @{ Name = "python3"; Args = @() }
  )

  foreach ($candidate in $candidates) {
    $cmd = Get-Command $candidate.Name -ErrorAction SilentlyContinue
    if ($cmd) {
      return [pscustomobject]@{
        Command = $candidate.Name
        Args = $candidate.Args
      }
    }
  }

  throw "Python was not found in PATH. Please install Python 3.10+ and make sure `py`, `python`, or `python3` is available in the terminal."
}

$venvPython = Join-Path $venv "Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
  $bootstrapPython = Resolve-BootstrapPython
  & $bootstrapPython.Command @($bootstrapPython.Args + @("-m", "venv", $venv))
  if ($LASTEXITCODE -ne 0) {
    throw "Failed to create shared virtual environment at $venv. Please verify that Python can create virtual environments on this machine."
  }
}

if (-not (Test-Path $venvPython)) {
  throw "Shared virtual environment was not created successfully: $venvPython"
}

$python = $venvPython

& $python -m pip install --upgrade pip setuptools wheel
if ($LASTEXITCODE -ne 0) {
  throw "Failed to upgrade pip in shared virtual environment: $python"
}

function Install-RequirementFileLight {
  param(
    [string]$RequirementFile
  )

  if (-not (Test-Path $RequirementFile)) {
    return
  }

  $temp = Join-Path $env:TEMP ("colong-lite-" + [System.IO.Path]::GetRandomFileName() + ".txt")
  $skipPrefixes = @(
    "sentence-transformers",
    "torch",
    "torchvision",
    "torchaudio",
    "transformers",
    "safetensors",
    "scikit-learn",
    "scipy",
    "threadpoolctl",
    "joblib",
    "networkx"
  )

  $lines = Get-Content $RequirementFile | Where-Object {
    $line = ($_ | Out-String).Trim()
    if (-not $line -or $line.StartsWith("#")) { return $true }
    foreach ($prefix in $skipPrefixes) {
      if ($line -like "$prefix*") { return $false }
    }
    return $true
  }

  Set-Content -Path $temp -Value $lines -Encoding UTF8
  try {
    & $python -m pip install -r $temp
    if ($LASTEXITCODE -ne 0) {
      throw "Failed to install requirements from $RequirementFile"
    }
  } finally {
    Remove-Item $temp -Force -ErrorAction SilentlyContinue
  }
}

Install-RequirementFileLight -RequirementFile (Join-Path $root "apps\auth-portal\requirements.txt")
Install-RequirementFileLight -RequirementFile (Join-Path $root "apps\multiagent\requirements.txt")
Install-RequirementFileLight -RequirementFile (Join-Path $root "apps\multiagent\local_web_portal\requirements.txt")
Install-RequirementFileLight -RequirementFile (Join-Path $root "apps\novelclaw\requirements.txt")
Install-RequirementFileLight -RequirementFile (Join-Path $root "apps\novelclaw\local_web_portal\requirements.txt")

Write-Host "[ok] shared venv ready: $python"
