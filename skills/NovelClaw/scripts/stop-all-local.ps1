$ErrorActionPreference = "Stop"

$ports = 8010, 8011, 8012

foreach ($port in $ports) {
  $listeners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
  if (-not $listeners) {
    Write-Host "[skip] no listener on :$port"
    continue
  }

  foreach ($listener in $listeners) {
    try {
      $proc = Get-Process -Id $listener.OwningProcess -ErrorAction SilentlyContinue
      Stop-Process -Id $listener.OwningProcess -Force -ErrorAction Stop
      Write-Host "[stopped] :$port pid=$($listener.OwningProcess) $($proc.ProcessName)"
    } catch {
      Write-Host "[warn] failed to stop :$port pid=$($listener.OwningProcess)"
    }
  }
}
