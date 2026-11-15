@echo off
rem Prueba de 0.8.9 con todo junto, para un monitor de 144 Hz con FreeSync:
rem   - pantalla completa, 60 FPS reales, FIFO; con la generacion de fotogramas el monitor marca unos 120 Hz
rem     con FreeSync activo y no debe haber tirones al girar la camara (PACE-AMD-01).
rem   - FSR 4 Native AA + generacion de fotogramas: unos 120 fps en pantalla; el HUD no debe dejar estela.
rem   - miniaturas de fotos en HD: la vista previa al hacer una foto y la foto grande al abrir una carpeta.
rem   - sombras segun la resolucion 3D.
rem newsnap.ini no se modifica; el log queda en logs\pruebas\8-todo-0.8.9.log.
call "%~dp0_prueba.bat" 8-todo-0.8.9 AC_FULLSCREEN=1 AC_FPS=60 AC_VK_PRESENT=fifo AC_UPSCALING=fsr4 AC_UPSCALING_QUALITY=native AC_FRAME_GEN=fsr AC_HD_PHOTOS=1 AC_SHADOW_SCALE=auto AC_ASPECT=fit
