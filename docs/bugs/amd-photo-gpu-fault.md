# FOTO-01 · Fotos con bandas y cierres «write invalid» en RX 6900 XT (0.6)

Estado: **EN CURSO** · Responsable: MatyMeatBoy · 2026-11-14
**Causa no acreditada.** Este informe deja una corrección candidata sin probar
en AMD y un diagnóstico siempre activo en el log para que la próxima sesión en
la RX 6900 XT lo decida.

## Evidencia del propietario (RX 6900 XT, runtime 0.6 real)

Copias locales en `build/user-reports/rx6900xt-0.6/` (no se suben):
`logs/newsnap.1cambieconfigs.log`, `logs/newsnap.nivel1tomefoto.log`,
`album-bands-0.6.webp`.

- Los dos logs son del runtime 0.6 (`snap_render`, `snap_supersample`,
  `snap_random_range`, proveedores FSR oficiales, `log: …/logs/newsnap.log`),
  controlador AMD 26.10.1 de la rama RDNA 1/2. Ya no es el runtime 0.1.x del
  informe `keyboard-after-photo.md`.
- Ambos terminan igual: `vk: device fault: "GPU fault"` con
  `write invalid at 0x…, precision 0x1000`. Es la GPU escribiendo en una página
  sin respaldo, no una excepción de CPU ni un fatal del runtime.
- Sesión 1: el propietario cambió ajustes gráficos (FSR 3.1 → FSR 4, modo de
  presentación) y el fallo llegó después, siguiendo el tutorial. Sesión 2: sin
  cambiar ajustes, FSR 4 activo desde el inicio; el fallo llegó al hacer la
  primera foto del primer nivel, con la imagen ya corrupta en pantalla.
- La captura del álbum (misma sesión 2, fotos hechas a las 02:12) muestra
  franjas horizontales con contenido real de la foto y negro en el resto; las
  franjas empiezan y acaban a mitad de fila.
- No hay líneas `pool_bounds:`: en esa máquina ninguna imagen pidió más memoria
  que su almacenamiento NVN. La pista de `amd-photo-bands-lead.md` queda
  **descartada para Snap**: además el juego no usa pools físicos ni virtuales
  (`physical 0 pools, virtual 0 pools`), así que ninguna imagen comparte memoria
  con un pool.

## Qué hace el juego al guardar una foto (medido en RTX 4060, 0.6)

Traza `AC_TRACE=gfx` de la ruta de fotos (`build/foto01-trace-gfx/`):

1. Crea un pool nuevo sobre memoria recién reservada del montón del juego
   (`flags 0x24`, CPU_CACHED|GPU_CACHED): 0x5ef000 bytes para la foto y 0x5e000
   para la miniatura. Es el mismo objeto pool, inicializado dos veces.
2. `nvnCommandBufferCopyTextureToBuffer` de la textura 1080×720 RGBA8 (y de la
   de 240×200) a ese pool, en un envío propio.
3. Espera con `nvnQueueFenceSync`/`nvnSyncWait`/`nvnQueueFinish` (no usa
   `nvnCommandBufferFenceSync`), lee los bytes, codifica el JPEG y finaliza el
   pool.

En el runtime ese destino es un **buffer importado por puntero de host**
(`VK_EXT_external_memory_host`) sobre las páginas del juego, sin mirror: la
línea nueva lo confirma en RTX («destination … through the pool's own buffer»).
La GPU escribe directamente en páginas de memoria del proceso recién reservadas.

## Descartado con pruebas (todas en RTX 4060; ninguna vale como prueba AMD)

| Hipótesis | Resultado | Evidencia |
|---|---|---|
| El juego lee antes de que la copia termine por un fence equivocado | Descartada | Usa `QueueFenceSync`, cuyo valor cubre el envío; traza `foto01-trace-gfx` |
| El escalador temporal estropea la foto | No reproduce | Ruta de 540 s con FSR 3.1 Native AA: 4 copias con 0 bytes distintos y 0 filas negras, salida 0 (`foto01-fsr3-540`) |
| Dibujos omitidos mientras compila el pipeline (modo de AMD) | No reproduce | `AC_GPL=0` y caché de pipelines vacía: foto completa (`foto01-gpl0-cold`) |
| Imágenes que comparten memoria con un pool | Descartada para Snap | Sin pools físicos/virtuales; sin líneas `pool_bounds:` en AMD |
| ASTC sin soporte nativo | No distingue | La RTX tampoco lo tiene y usa el mismo decodificador en GPU; la foto es RGBA8 |

FSR 4 no se puede ejecutar en la RTX (el proveedor lo aporta el controlador de
AMD), y las dos sesiones con fallo lo tenían activo. No hay prueba a favor ni en
contra de que intervenga.

## Hipótesis de trabajo (sin comprobar)

El controlador de AMD para Windows falla al escribir desde la GPU en parte de
las páginas de un buffer importado por puntero de host cuando esas páginas
acaban de reservarse. Explicaría a la vez:

- las franjas: páginas de 4 KiB ≈ una fila de 1080 px RGBA; tramos de páginas
  escritas y no escritas dan bandas que empiezan y acaban a mitad de fila;
- el `write invalid … precision 0x1000`: una escritura de GPU a una página sin
  respaldo;
- que solo ocurra en AMD y que los bytes guardados ya lleven las bandas.

El donor ya evita esas importaciones en Linux y Wine («shadow storage»,
`AC_SHADOW`), por un problema distinto con `amdgpu`. En Windows nativo estaban
activas.

## Cambios de este PR

`newsnap/photo_readback_adapt.py` (reserva de FOTO-01):

1. **Diagnóstico siempre activo en el log, sin ajustes.** Cada copia de textura
   a buffer con tamaño de foto escribe dos líneas (máximo 24 copias por sesión):
   - `photo_log: copy …`: textura origen (propiedad GPU, subidas desde memoria,
     si su almacenamiento se escribió después), destino, clase de memoria, si
     va por el buffer del pool o por un mirror, y el escalador activo;
   - `photo_trace: gpu-t2b …`: bytes distintos entre la imagen origen y lo que
     llegó al buffer, filas negras, **teselas negras de 16 px** en origen/buffer
     y los primeros tramos negros del buffer (`y<fila>:x<ini>-<fin>`).
   Coste: dos copias a staging por foto. Los PNG siguen saliendo solo con
   `NEWSNAP_PHOTO_TRACE_DIR`.
2. **Candidata de corrección:** en GPU AMD sobre Windows, los pools visibles por
   CPU usan el almacenamiento shadow del donor en lugar de importar punteros de
   host. `AC_SHADOW=0` vuelve a las importaciones; `AC_SHADOW=1` lo fuerza en
   cualquier GPU. El log lo anuncia con `mem: AMD GPU on Windows: shadow
   storage…`.

## Pruebas ejecutadas

- `python -m unittest tests.test_photo_readback`: 3 OK. El fixture nativo cubre
  el modo solo-log, una banda parcial (`black_tiles16=0/7`, un tramo
  `y32:x16-127`) y el tope de capturas.
- Runtime privado compilado desde este árbol con el kit 0.6
  (`build/foto01-build`): selftest y cargador del candidato OK.
- Ruta de fotos de 400 s en RTX 4060 con ese binario y sin ajustes
  (`build/foto01-newbin`): salida 0, cuatro pares de líneas, 0 bytes distintos,
  0 teselas negras.
- Ruta de fotos de 400 s en RTX 4060 con el 0.6 publicado y `AC_SHADOW=1`
  (`build/foto01-shadow1`): salida 0, fotos sin diferencias. Es el camino que
  la candidata activa en AMD.

## Cómo leer el próximo log de la RX 6900 XT

| Línea `photo_trace: gpu-t2b` | Lectura |
|---|---|
| `mismatch_bytes=0` y `black_tiles16=0/0` | La copia llegó completa; si el álbum sigue con bandas, el daño es posterior (codificación o carga) |
| `mismatch_bytes>0`, teselas negras solo en el buffer | La textura estaba bien y la copia al buffer perdió datos: confirma la hipótesis de la importación |
| Teselas negras ya en el origen | La textura de la foto se dibujó mal antes de copiarla: otra causa (render), no la importación |

Prueba inmediata en la 0.6 ya instalada, sin binario nuevo: añadir `shadow = 1`
a `newsnap.ini` (o la variable de entorno `AC_SHADOW=1`) y repetir la foto del
primer nivel. Para separar FSR 4: repetir además con el escalador en FSR 3.1.

## Límites

- Nada de esto se ha ejecutado en AMD. La candidata puede no cambiar nada.
- El modo shadow copia memoria por CPU en cada envío. En RTX la ruta mantuvo
  ≈60 fps de media; no se hizo comparación de rendimiento controlada y no hay
  medida en AMD.
- `shadow = 1` en `newsnap.ini` se aplica aunque el log lo anote como clave
  desconocida.
- El cierre de la sesión 1 no ocurrió al hacer una foto; no está demostrado que
  comparta causa con el de la sesión 2.
