@echo off
setlocal
cd /d "%~dp0.."
set "GPS_DAY=%~1"
if not defined GPS_DAY set /p "GPS_DAY=Fecha del reporte (AAAA-MM-DD): "
if not defined GPS_DAY exit /b 1
".venv\Scripts\python.exe" -m gps_demo onway --date "%GPS_DAY%"
if errorlevel 1 (
  echo No se genero el lote. Revisar el error anterior.
  pause
  exit /b 1
)
echo Reportes guardados dentro de outputs\reportes
pause
