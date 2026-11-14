@echo off
rem Todas las sospechas a la vez. Si sigue fallando, salta a la 6: las pruebas 2 a 5 no hacen falta.
call "%~dp0_prueba.bat" 1-todo-conservador "AC_REPLAY_ASYNC=0" "AC_PIPE_SKIP=strict" "AC_ASTC=cpu" "AC_UPSCALING=off" "AC_TEX_ALIAS=0" "AC_TEX_PREFETCH=0" "AC_MEMORY=import" "AC_VK_PRESENT=fifo"
