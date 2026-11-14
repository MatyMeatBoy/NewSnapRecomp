@echo off
rem Pruebas A/B de NewSnapRecomp para la RX 6900 XT (FOTO-01).
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
if not defined JUEGO (
  echo No encuentro newsnap.exe. Copia la carpeta pruebas-amd junto a newsnap.exe.
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
