# Traspaso: depuración directa en la RX 6900 XT

2026-11-14 · Para la sesión que trabaje en el PC con AMD. Resume lo que ya se
sabe y qué hacer primero, para no repetir pruebas. Detalle y evidencia en
`amd-photo-gpu-fault.md` e `integration-07.md`.

## Qué falla (solo en la RX 6900 XT, controlador 26.10.1, rama RDNA 1/2)

1. **Miniatura de la foto dentro del nivel** con franjas negras de patrón fijo:
   1 de cada 4 tramos con imagen, igual en fotos distintas. Las fotos guardadas
   salen igual.
2. **Tiras en la interfaz:** retrato del profesor, placa del nombre, marco del
   visor. Con presentación `fifo` el retrato sale bien.
3. **Cuadrados** que GPU-WRITE-01 había corregido en el tutorial, de vuelta.
4. **Cierres** con `vk: device fault … write invalid`: tres logs, los tres con
   FSR 4 Native AA activo, uno de ellos con shadow activo.

En RTX 4060 nada de esto ocurre con el mismo runtime.

## Ya descartado (no repetir)

| Hipótesis | Cómo se descartó |
|---|---|
| Importación por puntero de host | `shadow = 1` en AMD: mismo aspecto y otro fault |
| Fence equivocado al leer la foto | El juego usa `QueueFenceSync`; traza en RTX |
| ASTC sin soporte nativo, por sí solo | La RTX tampoco lo tiene y usa el mismo decodificador |
| Alias de imágenes con memoria de pool | Snap no usa pools físicos ni virtuales |
| FSR 4 como causa de las franjas | Con el escalador apagado la miniatura sigue rota |

No reproducido en RTX forzando el camino de AMD (no vale como descarte en AMD):
`AC_GPL=0` con caché de pipelines vacía; FSR 3.1 Native AA; la combinación
conservadora completa.

## Primer paso en AMD: volcado del fotograma

Es el dato que falta. Con el defecto visible:

```
set AC_DUMP_KEY=1
set AC_DUMP_N=2
newsnap.exe        (F12 con la miniatura rota en pantalla)
```

`dump/passes.txt` lista cada pase, sus destinos, texturas (dirección, estado de
mirror, número de subidas) y los shaders; los PNG muestran qué pase produce ya
la imagen rota. Buscar la textura 1080×720 RGBA8 de la foto: si el PNG del pase
que la dibuja ya tiene franjas, el fallo está en ese pase (shader, pipeline,
destino); si sale completa y la que se muestrea después no, está entre medias
(copia, alias, subida desde memoria).

`AC_DUMP_DRAWS=<seq>` parte ese pase dibujo a dibujo. `AC_TRACE=gfx` da una
línea por fotograma con pases, dibujos, copias y dispatch.

## Segundo paso: descarte por ajustes (`tools/pruebas-amd/`)

Seis `.bat` en orden. El primero aplica todas las sospechas a la vez; si con él
sigue fallando, ninguna lo es y solo queda el volcado. Cada log lleva una línea
`amd_diag:` con los ajustes efectivos.

Sospechas, de más a menos probable según las capturas (estimación, no medida):

1. Carrera con la reproducción en su propio hilo (`AC_REPLAY_ASYNC=0`).
2. Dibujos omitidos mientras compila su pipeline: en RDNA 2 la biblioteca de
   pipelines está apagada y `AC_PIPE_SKIP=fullscreen` omite en lugar de esperar
   (`AC_PIPE_SKIP=strict`). Probar también `AC_GPL=1`, que es el camino de NVIDIA.
3. Decodificador ASTC por cómputo (`AC_ASTC=cpu`), para las tiras de interfaz.
4. Shaders de cómputo del juego: dentro del nivel hay 10–40 dispatch por
   fotograma. En AMD el traductor usa subgrupos de 64 (32 fijado en cómputo) y
   buffers de almacenamiento con alineación 4; en NVIDIA 32 y 16. Sin ajuste
   propio: mirar en el volcado las imágenes y buffers que escriben.
5. FSR 4 solo para los cierres (`AC_UPSCALING=fsr3`).

## Reproducir sin pasar el tutorial a mano

`tests/routes/photo-tutorial-expedition.txt` recorre tutorial, registro de dos
fotos, evaluación y la primera expedición (540 s a 60 fps) con entradas
programadas. Requiere un perfil **copiado** que ya haya pasado la configuración
inicial:

```
set AC_INPUT=none
set AC_INPUT_SCRIPT=<ruta al archivo de ruta>
set AC_FPS=60
set AC_VK_PRESENT=fifo
newsnap.exe --exefs <GameData>\exefs --romfs <GameData>\romfs --profile <copia del perfil> --seconds 540
```

Las fotos se registran hacia el fotograma 20178 y 20988; la expedición empieza
hacia el 21170. `AC_SHOTS=w330-535:5` con `AC_SHOTS_DIR` guarda capturas (frenan
el juego: no sirven para medir ritmo).

## Reglas que siguen vigentes

- No tocar partidas, fotos, imports ni claves del propietario: trabajar sobre
  copias en `build/`. No subir datos del juego, volcados ni ejecutables.
- No cambiar la lógica del juego para saltar pasos.
- Una prueba en AMD no valida NVIDIA ni al revés; anotar siempre GPU,
  controlador y la línea `amd_diag:`.
- Una sola prueba GPU a la vez.
