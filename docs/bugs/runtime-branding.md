# Identidad visible del runtime y configuración portable

El runtime heredaba nombres del donor en el log automático y sus rotaciones:
`logs/astralchain.log` y `totk.N.log`. Los mensajes de crash también identificaban
direcciones host como `astralchain+offset`, aunque el ejecutable del port es
`newsnap.exe`. Los avisos sobre DLL, preparación, RomFS y algunas traducciones
tenían la misma referencia engañosa.

`newsnap/branding_adapt.py` aporta 49 reemplazos literales en 12 archivos. Cada
ancla debe aparecer exactamente una vez mediante el contrato `replace_once` del
adaptador. El donor permanece intacto. Los mensajes, identificador SDL/Linux y
cabeceras de diagnóstico pasan a usar NewSnap/newsnap; comentarios internos,
atribuciones MIT/copyright, variables compatibles `AC_*` y claves internas de
prueba NGX se conservan. El menú ya construye su versión Snap directamente;
también se limpian las cuatro traducciones heredadas de esa cadena y los avisos
traducidos de ubicación del ejecutable, sin cambiar las opciones del menú.

La familia nueva es `logs/newsnap.log` y `newsnap.1.log` … `newsnap.4.log`. Se
conservan exactamente el algoritmo, número de rotaciones, reemplazo de colisiones,
límite de tamaño y comportamiento ante stderr redirigido. No se buscan, renombran,
borran ni incorporan logs antiguos: quedan disponibles para diagnóstico.

## Compatibilidad de configuración

El runtime busca `newsnap.ini` junto al ejecutable, con comprobación de capacidad
incluido el terminador. Solo si ese nombre **no existe** intenta leer el antiguo
`astralchain.ini`. Un archivo nuevo vacío, malformado o ilegible conserva prioridad;
un error de lectura no activa una configuración antigua silenciosamente.

La carga no escribe archivos. `cfg_save()` apunta siempre al nombre nuevo. Si se
cargó únicamente el antiguo y el nuevo todavía no existe, el guardado usa las
líneas antiguas como base de lectura y aplica el algoritmo original de claves
cambiadas al destino nuevo. Esto conserva comentarios, finales de línea, claves
desconocidas y preferencias no modificadas; importar las claves como limpias y
guardar solamente la modificada habría perdido las demás en el siguiente inicio.
Si la base antigua ya no puede leerse, el guardado falla sin crear un resultado
parcial. El archivo antiguo nunca se escribe ni elimina. El guardado sin cambios
conserva su contrato anterior: éxito sin crear un archivo innecesario.

La selección de archivos/configuración del launcher se integra por separado por
el coordinador; este adaptador no modifica el launcher ni su estado persistido.

## Pruebas y límites

`python -m unittest tests.test_branding`: cuatro pruebas, con fixtures nativos
compilados mediante Clang sobre el código real del donor adaptado:

- `log_open` con archivos sintéticos: rotación completa, colisión en la última
  ranura y conservación byte a byte de los logs anteriores.
- `cfg.c` completo con shims de plataforma: carga antigua, prioridad nueva,
  nuevo vacío/malformado/ilegible, fallo posterior al leer la base antigua,
  guardado conservando preferencias/comentarios/CRLF y límites exactos del buffer.
- Las 49 anclas coinciden una vez; las atribuciones se conservan y los mensajes
  cubiertos dejan de mencionar ejecutables de otros juegos.

Antes del cambio fallaron las aserciones nativas de nombre de log, conservación
del INI antiguo, prioridad del nuevo y etiquetas visibles. Tras el cambio todas
pasan. Los shims verifican el flujo de la configuración y el destino del guardado;
no prueban la atomicidad real de la plataforma ante corte de alimentación. No se
ejecutó el juego, una GPU ni dispositivos físicos. El coordinador debe verificar
`adapt_sources` completo y la compilación integrada antes de cerrar la tarea.
El teclado/software keyboard queda fuera de este cambio, reservado a MatyMeatBoy.
