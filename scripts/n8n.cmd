@echo off
setlocal
cd /d "%~dp0.."
if not defined GPS_NODE if exist ".runtime\node24\node.exe" set "GPS_NODE=%CD%\.runtime\node24\node.exe"
if not defined GPS_NODE if exist "%USERPROFILE%\tools\nodejs\node.exe" set "GPS_NODE=%USERPROFILE%\tools\nodejs\node.exe"
if not defined GPS_NODE set "GPS_NODE=node"
if not exist ".runtime\n8n\node_modules\n8n\bin\n8n" (
  echo Instalar n8n local segun GUIA_PROYECTO.md antes de iniciar.
  exit /b 1
)
set "N8N_USER_FOLDER=%CD%\.runtime\state"
set "N8N_HOST=127.0.0.1"
set "N8N_LISTEN_ADDRESS=127.0.0.1"
set "N8N_DIAGNOSTICS_ENABLED=false"
set "N8N_PERSONALIZATION_ENABLED=false"
set "N8N_RUNNERS_BROKER_LISTEN_ADDRESS=127.0.0.1"
set "GENERIC_TIMEZONE=America/Lima"
set "TZ=America/Lima"
"%GPS_NODE%" ".runtime\n8n\node_modules\n8n\bin\n8n" start
exit /b %errorlevel%
