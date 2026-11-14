@echo off
rem Todas las opciones conservadoras a la vez. Si aqui sale bien, alguna de las anteriores es la causa.
call "%~dp0_prueba.bat" 30-todo-conservador "AC_REPLAY_ASYNC=0" "AC_TEX_ALIAS=0" "AC_MEMORY=import" "AC_TEX_PREFETCH=0" "AC_PIPE_SKIP=strict" "AC_ASTC=cpu" "AC_UPSCALING=off" "AC_VK_PRESENT=fifo"
