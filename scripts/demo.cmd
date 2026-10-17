@echo off
setlocal
cd /d "%~dp0.."
".venv\Scripts\python.exe" -m gps_demo run
exit /b %errorlevel%
