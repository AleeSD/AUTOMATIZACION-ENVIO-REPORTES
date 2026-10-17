$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$logs = Join-Path $projectRoot '.runtime\logs'
New-Item -ItemType Directory -Path $logs -Force | Out-Null
$service = $null
try {
    $service = Invoke-RestMethod 'http://127.0.0.1:8766/health' -TimeoutSec 2
} catch { }
if ($service -and $service.service -ne 'gps-daily') { throw 'El puerto 8766 pertenece a otra aplicacion' }
if (-not $service) {
    $python = Join-Path $projectRoot '.venv\Scripts\python.exe'
    $process = Start-Process -FilePath $python -ArgumentList '-m gps_demo.daily serve' -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logs 'gps.out.log') -RedirectStandardError (Join-Path $logs 'gps.error.log')
    $process.Id | Set-Content -LiteralPath (Join-Path $projectRoot '.runtime\gps.pid')
}
try {
    Invoke-WebRequest 'http://127.0.0.1:5678/healthz' -UseBasicParsing -TimeoutSec 2 | Out-Null
} catch {
    $node = Join-Path $projectRoot '.runtime\node24\node.exe'
    $entry = Join-Path $projectRoot '.runtime\n8n\node_modules\n8n\bin\n8n'
    $env:N8N_USER_FOLDER = Join-Path $projectRoot '.runtime\state'
    $env:N8N_HOST = '127.0.0.1'
    $env:N8N_LISTEN_ADDRESS = '127.0.0.1'
    $env:N8N_DIAGNOSTICS_ENABLED = 'false'
    $env:N8N_PERSONALIZATION_ENABLED = 'false'
    $env:N8N_RUNNERS_BROKER_LISTEN_ADDRESS = '127.0.0.1'
    $env:GENERIC_TIMEZONE = 'America/Lima'
    $env:TZ = 'America/Lima'
    $env:PATH = (Split-Path -Parent $node) + ';' + $env:PATH
    $process = Start-Process -FilePath $node -ArgumentList @(('"'+$entry+'"'), 'start') -WorkingDirectory $projectRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logs 'n8n.out.log') -RedirectStandardError (Join-Path $logs 'n8n.error.log')
    $process.Id | Set-Content -LiteralPath (Join-Path $projectRoot '.runtime\n8n.pid')
}
Write-Host 'Inicio solicitado. n8n: http://127.0.0.1:5678 ; estado: outputs\ESTADO_AUTOMATIZACION.json'
