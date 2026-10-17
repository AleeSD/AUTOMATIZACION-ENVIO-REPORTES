$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
foreach ($name in @('gps', 'n8n')) {
    $pidFile = Join-Path $projectRoot ('.runtime\' + $name + '.pid')
    if (-not (Test-Path -LiteralPath $pidFile)) { continue }
    $processId = [int](Get-Content -LiteralPath $pidFile -Raw)
    $details = Get-CimInstance Win32_Process -Filter "ProcessId=$processId" -ErrorAction SilentlyContinue
    if ($null -eq $details) { continue }
    $expected = if ($name -eq 'gps') { Join-Path $projectRoot '.venv\Scripts\python.exe' } else { Join-Path $projectRoot '.runtime\node24\node.exe' }
    if ($details.ExecutablePath -ne $expected) { throw 'El PID guardado no corresponde al proceso local esperado; no se detuvo' }
    if ($name -eq 'gps' -and $details.CommandLine -notmatch 'gps_demo.daily') { throw 'Comando Python distinto al esperado' }
    if ($name -eq 'n8n' -and -not $details.CommandLine.Contains((Join-Path $projectRoot '.runtime\n8n\node_modules\n8n\bin\n8n'))) { throw 'Comando n8n distinto al esperado' }
    $children = Get-CimInstance Win32_Process -Filter "ParentProcessId=$processId" -ErrorAction SilentlyContinue
    foreach ($child in $children) {
        $owned = if ($name -eq 'gps') { $child.CommandLine -match 'gps_demo.daily' } else { $child.ExecutablePath -eq $expected -and $child.CommandLine.Contains($projectRoot) }
        if ($owned) { Stop-Process -Id $child.ProcessId -ErrorAction SilentlyContinue }
    }
    Stop-Process -Id $processId -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $pidFile
}
Write-Host 'Procesos de esta automatizacion detenidos.'
