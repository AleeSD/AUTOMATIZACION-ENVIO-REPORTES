param([string]$Lote, [switch]$Enviar, [switch]$VentanaConfirmada)
$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Security\Microsoft.PowerShell.Security.psd1') -ErrorAction Stop
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not $Lote) {
    $Lote = & $pythonPath -c 'from gps_demo.whatsapp import latest_batch; print(latest_batch())'
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
& $pythonPath -m gps_demo.whatsapp --batch $Lote
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
if (-not $Enviar) { exit 0 }
if (-not $VentanaConfirmada) {
    $answer = Read-Host 'Los tres receptores ya escribieron al REMITENTE META hace menos de 24 horas? Escribe SI solo si confirmaste las respuestas'
    if ($answer -cne 'SI') { Write-Host 'No se realizo ningun envio.'; exit 1 }
}
$settings = Get-Content -LiteralPath (Join-Path $projectRoot 'config\meta.local.json') -Raw | ConvertFrom-Json
$secureToken = ConvertTo-SecureString $settings.token_protected
$previousToken = $env:META_ACCESS_TOKEN
$previousId = $env:META_PHONE_NUMBER_ID
$previousVersion = $env:META_GRAPH_VERSION
$pointer = [IntPtr]::Zero
try {
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureToken)
    $env:META_ACCESS_TOKEN = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
    $env:META_PHONE_NUMBER_ID = $settings.phone_number_id
    $env:META_GRAPH_VERSION = $settings.graph_version
    & $pythonPath -m gps_demo.whatsapp --batch $Lote --send --window-confirmed
    $resultCode = $LASTEXITCODE
} finally {
    if ($pointer -ne [IntPtr]::Zero) { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
    $secureToken.Dispose()
    $env:META_ACCESS_TOKEN = $previousToken
    $env:META_PHONE_NUMBER_ID = $previousId
    $env:META_GRAPH_VERSION = $previousVersion
}
exit $resultCode
