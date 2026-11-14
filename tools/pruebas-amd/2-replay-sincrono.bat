@echo off
rem Sospecha principal: carrera entre el juego y el hilo que dibuja (el retrato cambia con el modo de presentacion).
call "%~dp0_prueba.bat" 2-replay-sincrono "AC_REPLAY_ASYNC=0"
