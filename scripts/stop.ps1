$ErrorActionPreference = 'Stop'
$rootDir = Split-Path -Parent $PSScriptRoot
$runDir = Join-Path $rootDir 'data\run'
foreach ($service in @(@{name='knowledge'},@{name='inbox'})) {
  $pidFile = Join-Path $runDir ($service.name + '.pid')
  if (-not (Test-Path $pidFile)) { continue }
  $record = Get-Content -LiteralPath $pidFile -Raw | ConvertFrom-Json
  $process = Get-Process -Id ([int]$record.pid) -ErrorAction SilentlyContinue
  if ($process) {
    $sameExecutable = [string]::Equals($process.Path,$record.executable,[StringComparison]::OrdinalIgnoreCase)
    $sameStartTime = $process.StartTime.ToUniversalTime().Ticks.ToString() -eq [string]$record.startedTicks
    if ($sameExecutable -and $sameStartTime) { Stop-Process -Id $process.Id -Force }
  }
  Remove-Item -LiteralPath $pidFile -Force
}
Write-Host 'Stopped the app services started by this project.'
