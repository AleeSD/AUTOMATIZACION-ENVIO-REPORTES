@echo off
setlocal
cd /d "%~dp0.."
if not defined GPS_PYTHON set "GPS_PYTHON=python"
"%GPS_PYTHON%" -m venv .venv
if errorlevel 1 exit /b 1
if exist requirements.lock.txt (
  ".venv\Scripts\python.exe" -m pip install -r requirements.lock.txt
) else (
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
)
exit /b %errorlevel%
