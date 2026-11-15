@echo off
rem Pruebas de NewSnapRecomp: arranca el juego con ajustes solo para esa vez y guarda el log.
rem Uso interno: _prueba.bat NOMBRE VARIABLE=VALOR [VARIABLE=VALOR ...]
rem Las variables solo valen para este arranque: newsnap.ini no se modifica.
setlocal EnableExtensions
set "NOMBRE=%~1"
if "%NOMBRE%"=="" (
  echo Falta el nombre de la prueba.
  pause
  exit /b 2
)
set "JUEGO="
if exist "%~dp0newsnap.exe" set "JUEGO=%~dp0"
if not defined JUEGO if exist "%~dp0..\newsnap.exe" set "JUEGO=%~dp0..\"
if not defined JUEGO if exist "%~dp0..\..\newsnap.exe" set "JUEGO=%~dp0..\..\"
if not defined JUEGO if exist "%~dp0..\GameData\newsnap.exe" set "JUEGO=%~dp0..\GameData\"
if not defined JUEGO if exist "%~dp0GameData\newsnap.exe" set "JUEGO=%~dp0GameData\"
if not defined JUEGO (
  echo No encuentro newsnap.exe. Deja la carpeta pruebas-amd junto a NewSnapLauncher.exe o junto a newsnap.exe.
  pause
  exit /b 3
)
shift
:variables
if "%~1"=="" goto arrancar
set "%~1"
echo   %~1
shift
goto variables
:arrancar
echo Prueba %NOMBRE%: arrancando el juego. Cierra el juego para terminar la prueba.
pushd "%JUEGO%"
rem Compila todos los shaders antes de jugar (la version mas completa: todas las bibliotecas mas las variantes ya vistas).
rem Solo cuando hace falta: no hay preparacion (una actualizacion que cambio los shaders la borra) o el runtime la pide.
set "PREPARAR="
if not exist "shader-prepared.bin" set "PREPARAR=1"
findstr /c:"\"shader_preparation_required\": true" "newsnap-game.json" >nul 2>&1 && set "PREPARAR=1"
if defined PREPARAR if exist "NewSnapLauncher.exe" (
  echo Preparando todos los shaders antes de jugar, solo esta vez...
  start "" /wait NewSnapLauncher.exe --prepare --all
)
start "" /wait newsnap.exe
set "SALIDA=%ERRORLEVEL%"
if not exist "logs\pruebas" mkdir "logs\pruebas"
if exist "logs\newsnap.log" copy /y "logs\newsnap.log" "logs\pruebas\%NOMBRE%.log" >nul
popd
echo.
echo Codigo de salida: %SALIDA%
echo Log guardado en logs\pruebas\%NOMBRE%.log
pause
exit /b %SALIDA%
