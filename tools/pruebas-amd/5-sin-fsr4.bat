@echo off
rem Para los cierres: los tres logs con fallo de GPU tenian FSR 4 activo. Juega un rato y saca fotos.
call "%~dp0_prueba.bat" 5-sin-fsr4 "AC_UPSCALING=fsr3"
