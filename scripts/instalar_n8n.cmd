@echo off
setlocal
cd /d "%~dp0.."
".venv\Scripts\python.exe" -m gps_demo.install_n8n
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m gps_demo.configure_n8n
exit /b %errorlevel%
