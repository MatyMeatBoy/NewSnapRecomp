@echo off
rem FreeSync sin generacion de fotogramas: pantalla completa, 60 FPS, FIFO.
rem Con FreeSync activo el menu del monitor deberia marcar unos 60 Hz (no 144) y girar la camara
rem no debe dar tirones. Si marca 144 fijos, FreeSync no se activo: prueba el limite "Segun la pantalla".
call "%~dp0_prueba.bat" 9-freesync-60 AC_FULLSCREEN=1 AC_FPS=60 AC_VK_PRESENT=fifo AC_FRAME_GEN=off AC_ASPECT=fit
