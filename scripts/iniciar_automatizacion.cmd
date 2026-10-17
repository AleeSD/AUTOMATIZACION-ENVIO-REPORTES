@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0iniciar_automatizacion.ps1"
exit /b %errorlevel%
