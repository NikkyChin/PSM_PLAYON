@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "PROJECT_PATH=C:\Users\psmra\PSM_PLAYON_PROD"
set "DB_FILE=%PROJECT_PATH%\db_prod.sqlite3"
set "BACKUP_PATH=%PROJECT_PATH%\backups"

if not exist "%BACKUP_PATH%" (
  echo ERROR: No existe la carpeta de backups:
  echo %BACKUP_PATH%
  echo.
  pause
  exit /b 1
)

rem --- Contar backups disponibles ---
set /a COUNT=0
for /f "delims=" %%F in ('dir /b /a:-d "%BACKUP_PATH%\backup_*.sqlite3" 2^>nul') do (
  set /a COUNT+=1
)

if "%COUNT%"=="0" (
  echo No hay backups para restaurar en:
  echo %BACKUP_PATH%
  echo.
  pause
  exit /b 1
)

echo.
echo ==== RESTAURAR BASE DE DATOS (PROD) ====
echo Carpeta de backups: %BACKUP_PATH%
echo Base actual:        %DB_FILE%
echo.
echo Backups disponibles:
echo.

rem --- Mostrar lista numerada (del mas nuevo al mas viejo) ---
set /a IDX=0
for /f "delims=" %%F in ('dir /b /a:-d /o:-d "%BACKUP_PATH%\backup_*.sqlite3"') do (
  set /a IDX+=1
  set "BKP_!IDX!=%%F"
  echo   !IDX!^) %%F
)

echo.
set /p CHOICE=Elegi el numero del backup a restaurar: 

rem --- Validaciones basicas ---
if "%CHOICE%"=="" (
  echo ERROR: No elegiste nada.
  echo.
  pause
  exit /b 1
)

for /f "delims=0123456789" %%A in ("%CHOICE%") do (
  echo ERROR: Opcion invalida. Solo numeros.
  echo.
  pause
  exit /b 1
)

if %CHOICE% LSS 1 (
  echo ERROR: Opcion invalida.
  echo.
  pause
  exit /b 1
)

if %CHOICE% GTR %IDX% (
  echo ERROR: Opcion fuera de rango.
  echo.
  pause
  exit /b 1
)

set "SELECTED=%BACKUP_PATH%\!BKP_%CHOICE%!"

if not exist "%SELECTED%" (
  echo ERROR: No se encontro el backup seleccionado:
  echo %SELECTED%
  echo.
  pause
  exit /b 1
)

echo.
echo Vas a RESTAURAR este backup:
echo %SELECTED%
echo.
set /p CONFIRM=Escribi SI para confirmar: 

if /I not "%CONFIRM%"=="SI" (
  echo Cancelado.
  echo.
  pause
  exit /b 0
)

rem --- Backup de seguridad del DB actual antes de pisar ---
if exist "%DB_FILE%" (
  for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-dd_HH-mm-ss"') do set "TS=%%i"
  set "SAFETY=%BACKUP_PATH%\pre_restore_%TS%.sqlite3"
  copy /Y "%DB_FILE%" "%SAFETY%" >nul
  if errorlevel 1 (
    echo ERROR: No se pudo crear el backup de seguridad.
    echo.
    pause
    exit /b 1
  )
  echo Backup de seguridad creado:
  echo %SAFETY%
  echo.
)

rem --- Restaurar ---
copy /Y "%SELECTED%" "%DB_FILE%" >nul
if errorlevel 1 (
  echo ERROR: Fallo la restauracion.
  echo.
  pause
  exit /b 1
)

echo.
echo ✅ Restauracion completada.
echo Base restaurada en:
echo %DB_FILE%
echo.
echo IMPORTANTE:
echo - Si el servidor estaba corriendo, reinicialo (cerrar el .bat de arranque y abrirlo de nuevo).
echo.
pause
