param(
  [switch]$Force
)

$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

$pairs = @(
  @{
    Name = "auth-portal"
    Source = Join-Path $root "state_snapshots\auth-portal\local_web_portal\data"
    Target = Join-Path $root "apps\auth-portal\local_web_portal\data"
  },
  @{
    Name = "multiagent-data"
    Source = Join-Path $root "state_snapshots\multiagent\local_web_portal\data"
    Target = Join-Path $root "apps\multiagent\local_web_portal\data"
  },
  @{
    Name = "multiagent-runs"
    Source = Join-Path $root "state_snapshots\multiagent\local_web_portal\runs"
    Target = Join-Path $root "apps\multiagent\local_web_portal\runs"
  },
  @{
    Name = "novelclaw-data"
    Source = Join-Path $root "state_snapshots\novelclaw\local_web_portal\data"
    Target = Join-Path $root "apps\novelclaw\local_web_portal\data"
  },
  @{
    Name = "novelclaw-runs"
    Source = Join-Path $root "state_snapshots\novelclaw\local_web_portal\runs"
    Target = Join-Path $root "apps\novelclaw\local_web_portal\runs"
  }
)

foreach ($pair in $pairs) {
  if (-not (Test-Path $pair.Source)) {
    Write-Host "[skip] $($pair.Name) snapshot not found: $($pair.Source)"
    continue
  }

  New-Item -ItemType Directory -Force -Path $pair.Target | Out-Null

  if ($Force.IsPresent -and (Test-Path $pair.Target)) {
    Get-ChildItem -Force $pair.Target | Remove-Item -Recurse -Force
  }

  Copy-Item (Join-Path $pair.Source "*") $pair.Target -Recurse -Force
  Write-Host "[ok] restored $($pair.Name) -> $($pair.Target)"
}

