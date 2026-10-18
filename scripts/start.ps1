$ErrorActionPreference = 'Stop'
$rootDir = Split-Path -Parent $PSScriptRoot
$python = Get-Command py -ErrorAction SilentlyContinue
if (-not $python) { throw 'Python was not found. Install Python 3.11 or newer, then reopen PowerShell.' }
$nodeCommand = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeCommand) { throw 'Node.js was not found. Install Node.js 22.6 or newer, then reopen PowerShell.' }
$nodeExecutable = $nodeCommand.Source
$nodeVersion = (& $nodeExecutable --version).Trim().TrimStart('v')
if ([version]$nodeVersion -lt [version]'22.6') { throw 'Install Node.js 22.6 or newer, then rerun this script.' }

function Get-LocalListenerId([int]$port) {
  $pattern = "^\s*TCP\s+127\.0\.0\.1:$port\s+\S+\s+LISTENING\s+(\d+)\s*$"
  foreach ($line in (netstat -ano -p tcp)) {
    if ($line -match $pattern) { return [int]$Matches[1] }
  }
  return $null
}

foreach ($port in @(8000,8001)) {
  $ownerId = Get-LocalListenerId $port
  if ($ownerId) { throw "Port $port is already in use by process $ownerId. Stop the old app with .\scripts\stop.ps1 or close the other service, then retry." }
}

$venvPython = Join-Path $rootDir '.venv\Scripts\python.exe'
if (-not (Test-Path $venvPython)) { & py -3 -m venv (Join-Path $rootDir '.venv') }
& $venvPython -m pip install -r (Join-Path $rootDir 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Python packages could not be installed. Check your internet connection and try again.' }

$runDir = Join-Path $rootDir 'data\run'
$logDir = Join-Path $rootDir 'data\logs'
New-Item -ItemType Directory -Force -Path $runDir,$logDir | Out-Null
$env:PYTHONPATH = $rootDir
$kbOut = Join-Path $logDir 'knowledge.log'
$kbErr = Join-Path $logDir 'knowledge-error.log'
$inboxOut = Join-Path $logDir 'inbox.log'
$inboxErr = Join-Path $logDir 'inbox-error.log'
$kbArgs = '-m uvicorn run_knowledge:app --host 127.0.0.1 --port 8000'
$inboxFile = Join-Path $rootDir 'task2-inbox-agent\src\server.ts'
$kbProcess = Start-Process -FilePath $venvPython -ArgumentList $kbArgs -WorkingDirectory $rootDir -WindowStyle Hidden -RedirectStandardOutput $kbOut -RedirectStandardError $kbErr -PassThru
$inboxProcess = Start-Process -FilePath $nodeExecutable -ArgumentList @('--experimental-strip-types',$inboxFile) -WorkingDirectory $rootDir -WindowStyle Hidden -RedirectStandardOutput $inboxOut -RedirectStandardError $inboxErr -PassThru
Set-Content -LiteralPath (Join-Path $runDir 'knowledge.pid') -Value (@{pid=$kbProcess.Id;startedTicks=$kbProcess.StartTime.ToUniversalTime().Ticks.ToString();executable=$venvPython} | ConvertTo-Json -Compress)
Set-Content -LiteralPath (Join-Path $runDir 'inbox.pid') -Value (@{pid=$inboxProcess.Id;startedTicks=$inboxProcess.StartTime.ToUniversalTime().Ticks.ToString();executable=$nodeExecutable} | ConvertTo-Json -Compress)

$ready = $false
for ($attempt=0; $attempt -lt 20; $attempt++) {
  try {
    $kb = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health' -TimeoutSec 2
    $inbox = Invoke-RestMethod -Uri 'http://127.0.0.1:8001/health' -TimeoutSec 2
    if ($kb.status -eq 'ok' -and $kb.retrieval -eq 'lexical' -and $inbox.status -eq 'ok' -and $inbox.service -eq 'inbox-agent') { $ready = $true; break }
  } catch { Start-Sleep -Seconds 1 }
}
if (-not $ready) {
  Write-Host 'The app did not start. Check data\logs\knowledge-error.log and data\logs\inbox-error.log.' -ForegroundColor Red
  throw 'Startup failed. Fix the error shown in the log, then run .\scripts\start.ps1 again.'
}
$kbOwner = Get-LocalListenerId 8000
$inboxOwner = Get-LocalListenerId 8001
if (-not $kbOwner -or -not $inboxOwner) { throw 'The health checks passed, but the service listener processes could not be identified.' }
foreach ($service in @(@{name='knowledge';id=$kbOwner},@{name='inbox';id=$inboxOwner})) {
  $ownerProcess = Get-Process -Id $service.id -ErrorAction Stop
  $record = [ordered]@{pid=$ownerProcess.Id;startedTicks=$ownerProcess.StartTime.ToUniversalTime().Ticks.ToString();executable=$ownerProcess.Path}
  Set-Content -LiteralPath (Join-Path $runDir ($service.name + '.pid')) -Value ($record | ConvertTo-Json -Compress)
}
Start-Process 'http://127.0.0.1:8000'
Write-Host 'The app is ready at http://127.0.0.1:8000. To stop it, run .\scripts\stop.ps1.' -ForegroundColor Green
