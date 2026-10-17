@echo off
setlocal
cd /d "%~dp0.."
".venv\Scripts\python.exe" -m gps_demo.daily run
exit /b %errorlevel%
