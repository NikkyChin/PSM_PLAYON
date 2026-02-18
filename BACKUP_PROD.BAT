@echo off
setlocal EnableExtensions

set "PROJECT_PATH=C:\Users\psmra\PSM_PLAYON_PROD"
set "DB_FILE=%PROJECT_PATH%\db_prod.sqlite3"
set "BACKUP_PATH=%PROJECT_PATH%\backups"

if not exist "%BACKUP_PATH%" mkdir "%BACKUP_PATH%"

if not exist "%DB_FILE%" (
  echo ERROR: No se encontro la base de datos:
  echo %DB_FILE%
  echo.
  pause
  exit /b 1
)

for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd_HH-mm-ss"') do set "TS=%%i"
set "FILENAME=backup_%TS%.sqlite3"

copy /Y "%DB_FILE%" "%BACKUP_PATH%\%FILENAME%" >nul
if errorlevel 1 (
  echo ERROR: Fallo la copia del backup.
  echo Origen: %DB_FILE%
  echo Destino: %BACKUP_PATH%\%FILENAME%
  echo.
  pause
  exit /b 1
)

echo.
echo Backup creado correctamente:
echo %BACKUP_PATH%\%FILENAME%
echo.
pause
