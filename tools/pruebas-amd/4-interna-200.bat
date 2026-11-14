@echo off
rem Resolucion interna 200 % (modo TV, sin reescalador). Saca fotos y mira HUD, fotos y miniaturas.
call "%~dp0_prueba.bat" 4-interna-200 "AC_RENDER_SCALE=200" "AC_UPSCALING=off" "AC_OPERATION_MODE=docked"
