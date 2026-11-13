# Prueba local del mando

La prueba muestra la identidad que SDL detecta, su GUID, si tiene un mapeo de
gamepad, los botones/ejes en vivo y las capacidades que informa el dispositivo.
Un joystick sin mapeo sigue apareciendo con sus controles originales. Una
capacidad de vibración significa que SDL la declara; la prueba no la activa.

Para comprobar el mando en el segundo PC:

1. Cierra el juego y abre la prueba de mandos del launcher.
2. Conecta el mando y comprueba nombre, GUID y reconocimiento. Si hay varios,
   revisa cada ID por separado.
3. Pulsa los botones y mueve ambas palancas y gatillos. Los botones deben volver
   a reposo al soltarlos. Los ejes se muestran como valores SDL originales:
   palancas aproximadamente de −32768 a 32767, gatillos mapeados de 0 a 32767.
4. Desconecta y vuelve a conectar el mando. La entrada anterior debe desaparecer;
   la nueva conexión puede recibir otro ID.
5. Cierra la prueba antes de abrir el juego, importar datos o reconstruir el
   runtime. Comprueba después los mismos controles dentro del juego.

Si no se reconoce como gamepad, anota nombre/GUID y los botones/ejes originales.
El archivo opcional `gamecontrollerdb.txt` va junto a `SDL3.dll` del runtime
(`GameData` en la instalación normal). Se usa la misma precedencia que el juego:
un `SDL_GAMECONTROLLERCONFIG_FILE` explícito suprime ese archivo local; cuando
se carga el archivo local, se reaplican los mapeos inline de
`SDL_GAMECONTROLLERCONFIG` para conservar las preferencias explícitas.

El diagnóstico no escribe partidas, perfiles ni bases de mandos; tampoco envía
entradas, activa sensores, LED o vibración. No hace falta abrir una ventana Vulkan
ni iniciar SDL video/audio/haptics. El launcher mantiene bloqueadas las operaciones
incompatibles mientras el diagnóstico posee SDL.

## Backend para el launcher

`newsnap.controller_probe.Session(runtime_dir, env=None)` inicializa el SDL
incluido en ese runtime. Usar constructor/context manager, `pump()`, `snapshot()`
y `close()` desde el hilo principal de Tk; SDL exige el hilo principal para
[inicializar subsistemas](https://wiki.libsdl.org/SDL3/SDL_Init) y
[procesar eventos](https://wiki.libsdl.org/SDL3/SDL_PumpEvents).

```python
with Session(runtime_dir, env=controller_environment) as session:
    controllers = session.snapshot()  # también hace pump
```

La UI debe poseer su estado ocupado y `ProfileLock` durante toda la sesión, y
programar snapshots con `after`, sin moverlos a un worker. `snapshot()` devuelve
una lista serializable a JSON con `id`, `name`, `guid`, `vendor`, `product`,
`recognized`, `virtual`, `connected`, `mapping`, `buttons`, `axes`, `raw_buttons`,
`raw_axes`, `hats`, `capabilities` y `error`. Una lista vacía significa que no hay
dispositivos enumerados. Una desconexión que coincide con una lectura puede
aparecer una vez con `connected=false`; el siguiente snapshot cierra su handle.
Los problemas globales generan `ProbeError`; las advertencias de mapeos están
en `session.warnings` y la versión en `session.sdl_version`.

Se abre una ruta absoluta a `SDL3.dll` con búsqueda segura de dependencias de
Windows. Se adquiere únicamente `SDL_INIT_GAMEPAD` (que implica joystick y
eventos). Cada handle abierto se cierra, los hints temporales se restauran, se
libera la referencia de subsistema y finalmente se descarga la DLL para permitir
reemplazar el runtime. No se usa `SDL_Quit` global.

## Evidencia automatizada

```powershell
python -m unittest tests.test_controller_probe -v
```

Las pruebas nativas usan copias temporales de la DLL incluida y joysticks
virtuales locales de SDL. Comprueban un gamepad mapeado y un joystick desconocido,
lecturas de botones/ejes/hat, múltiples dispositivos, desconexión, precedencia
de mapeos y descarga de DLL. Otra prueba compila los headers incluidos y compara
la ABI de `bool`, GUID, ID y descriptor virtual con ctypes. Las pruebas de fallo
verifican la limpieza de inicialización/hints/handles y la restricción de hilo.

Runtime verificado durante el desarrollo: SDL **3.4.18**, DLL SHA-256
`2b4b128d8d510cc2d442693cf848c050d700d43dc667afe9e5fd82b0570d667e`.
Esta evidencia virtual no confirma la compatibilidad física del mando del
segundo PC; esa aceptación depende de la prueba real y de su transporte USB o
Bluetooth.
