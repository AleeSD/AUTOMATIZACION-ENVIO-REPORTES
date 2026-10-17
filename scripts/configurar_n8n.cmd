@echo off
setlocal
cd /d "%~dp0.."
".venv\Scripts\python.exe" -m gps_demo.configure_n8n
exit /b %errorlevel%
