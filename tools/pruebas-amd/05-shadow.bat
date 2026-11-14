@echo off
rem La GPU no escribe en memoria importada del juego (ya probado: sin cambio).
call "%~dp0_prueba.bat" 05-shadow "AC_SHADOW=1"
