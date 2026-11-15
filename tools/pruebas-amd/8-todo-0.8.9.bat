@echo off
rem Prueba de 0.8.9 con todo junto, para el monitor de 144 Hz con FreeSync:
rem   - 144 FPS, pantalla completa, FIFO: con FreeSync el monitor sigue al juego, sin tirones.
rem   - Generacion de fotogramas FSR (FSR 4 Native AA) activada: solo genera si el juego baja de unos 79 fps.
rem     Al girar la camara no debe haber tirones y el HUD no debe dejar estela.
rem   - Miniaturas de fotos en HD: la vista previa al hacer una foto y la foto grande al abrir una carpeta.
rem   - Sombras segun la resolucion 3D.
rem newsnap.ini no se modifica; el log queda en logs\pruebas\8-todo-0.8.9.log.
call "%~dp0_prueba.bat" 8-todo-0.8.9 AC_FULLSCREEN=1 AC_FPS=144 AC_VK_PRESENT=fifo AC_UPSCALING=fsr4 AC_UPSCALING_QUALITY=native AC_FRAME_GEN=fsr AC_HD_PHOTOS=1 AC_SHADOW_SCALE=auto AC_ASPECT=fit
