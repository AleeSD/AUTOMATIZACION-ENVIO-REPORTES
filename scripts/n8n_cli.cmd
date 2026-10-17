@echo off
setlocal
cd /d "%~dp0.."
set "N8N_USER_FOLDER=%CD%\.runtime\state"
set "N8N_HOST=127.0.0.1"
set "N8N_LISTEN_ADDRESS=127.0.0.1"
set "N8N_DIAGNOSTICS_ENABLED=false"
set "N8N_PERSONALIZATION_ENABLED=false"
set "N8N_RUNNERS_BROKER_PORT=5680"
set "N8N_RUNNERS_BROKER_LISTEN_ADDRESS=127.0.0.1"
set "GENERIC_TIMEZONE=America/Lima"
set "TZ=America/Lima"
set "PATH=%CD%\.runtime\node24;%PATH%"
".runtime\node24\node.exe" ".runtime\n8n\node_modules\n8n\bin\n8n" %*
exit /b %errorlevel%
