$ErrorActionPreference = 'Stop'
Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Security\Microsoft.PowerShell.Security.psd1') -ErrorAction Stop
$projectRoot = Split-Path -Parent $PSScriptRoot
$secretPath = Join-Path $projectRoot 'config\meta.local.json'
$token = Read-Host 'Pega el TOKEN NUEVO de Meta (entrada oculta; no se envia al chat)' -AsSecureString
if ($token.Length -lt 20) { throw 'El token parece incompleto' }
$settings = @{
    phone_number_id = '1390443250816204'
    graph_version = 'v25.0'
    token_protected = ($token | ConvertFrom-SecureString)
}
$settings | ConvertTo-Json | Set-Content -LiteralPath $secretPath -Encoding UTF8
$token.Dispose()
Write-Host 'Token cifrado con Windows DPAPI para esta cuenta. No se envio ningun mensaje.'
Write-Host 'Para revisar el lote ejecuta scripts\whatsapp.cmd. Para enviar: scripts\whatsapp.cmd -Enviar'
