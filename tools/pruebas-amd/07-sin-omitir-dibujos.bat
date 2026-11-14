@echo off
rem Los dibujos esperan a su pipeline en vez de omitirse.
call "%~dp0_prueba.bat" 07-sin-omitir-dibujos "AC_PIPE_SKIP=strict"
