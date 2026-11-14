@echo off
rem Resolucion interna 150 % (modo TV, sin reescalador). Saca fotos y mira HUD, fotos y miniaturas.
call "%~dp0_prueba.bat" 3-interna-150 "AC_RENDER_SCALE=150" "AC_UPSCALING=off" "AC_OPERATION_MODE=docked"
