@echo off
setlocal
cd /d "%~dp0.."
set "GPS_DAY=%~1"
if not defined GPS_DAY set /p "GPS_DAY=Fecha de los reportes terminados (AAAA-MM-DD): "
if not defined GPS_DAY exit /b 1
".venv\Scripts\python.exe" -m gps_demo.daily ready --date "%GPS_DAY%"
exit /b %errorlevel%
