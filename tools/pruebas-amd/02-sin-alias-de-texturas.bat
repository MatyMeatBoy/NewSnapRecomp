@echo off
rem Una imagen nueva no hereda el contenido de otra en la misma direccion.
call "%~dp0_prueba.bat" 02-sin-alias-de-texturas "AC_TEX_ALIAS=0"
