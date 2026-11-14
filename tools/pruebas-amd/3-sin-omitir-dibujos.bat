@echo off
rem Camino propio de AMD RDNA2: dibujos omitidos mientras compila su pipeline (los cuadrados que volvieron).
call "%~dp0_prueba.bat" 3-sin-omitir-dibujos "AC_PIPE_SKIP=strict"
