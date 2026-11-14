@echo off
rem El dibujo se hace en el hilo del juego, sin cola aparte.
call "%~dp0_prueba.bat" 01-replay-sincrono "AC_REPLAY_ASYNC=0"
