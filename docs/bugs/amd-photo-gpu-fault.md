# FOTO-01 · Fotos con bandas y cierres «write invalid» en RX 6900 XT (0.6)

Estado: **EN CURSO** · Responsable: Claude · 2026-11-14
**Causa no acreditada.** Este informe deja un experimento opt-in sin probar en AMD y un diagnóstico
siempre activo en el log para acotar la próxima sesión en la RX 6900 XT.
No cambia el modo de memoria predeterminado de ninguna GPU.

**Actualización, mismo día:** la hipótesis de la importación por puntero de host quedó refutada por la
prueba del propietario con `shadow = 1`; ver «Segunda ronda». Sigue sin causa acreditada ni corrección.

## Segunda ronda del propietario (RX 6900 XT, 0.6, 2026-11-14)

Capturas locales en `build/user-reports/rx6900xt-0.6/` (`level-*.webp`).

- Con una partida ya guardada no hubo cierre, pero la **miniatura de la foto
  dentro del nivel** sale con las mismas franjas, antes de guardar nada. El
  defecto está en la textura de la foto en la GPU, no en la copia al guardar.
- Con `shadow = 1` en `newsnap.ini` el resultado es el mismo. No se recibió el
  log de esa sesión, así que falta confirmar la línea `mem: shadow storage…`.
- El patrón de franjas es **idéntico en fotos distintas**: en orden de memoria,
  uno de cada cuatro tramos tiene imagen y tres quedan en negro. Geometría fija.
- También salen con tiras el retrato del profesor, la placa del nombre del
  Pokémon y el marco del visor. Volvieron los «cuadrados» que GPU-WRITE-01 había
  corregido en el Pikachu del tutorial.
- Con presentación `fifo` (en lugar de `fifo_relaxed`) el retrato del profesor
  se ve bien y el resto sigue mal: al menos una parte depende del ritmo.
- Con el escalador apagado («Scaling bilinear») la miniatura sigue rota: FSR 4
  no es necesario para el defecto.

En RTX 4060, en el mismo nivel y con el mismo 0.6, miniatura, retrato y placa
salen limpios (`build/foto01-fsr3-540/shots/`). Traza `AC_TRACE=gfx` de la
expedición (`build/foto01-trace-540/`): la foto dentro del nivel **no usa
copias**; es un pase de dibujo más, y el juego lanza entre 10 y 40 shaders de
cómputo por fotograma. Nada de esto identifica aún la operación que falla en
AMD.

### Plan de pruebas en la RX 6900 XT (sin binario nuevo, de una en una)

Cada línea va en `newsnap.ini`; quitar la anterior antes de probar la siguiente.

| Ajuste | Qué separa |
|---|---|
| `replay_async = 0` | Carreras entre el juego y la reproducción en su propio hilo (lo sugiere la diferencia `fifo`/`fifo_relaxed`) |
| `tex_alias = 0` | Imágenes nuevas que heredan el contenido de otra en la misma dirección |
| `memory = import` | El mirror en VRAM de los pools usados como buffers |
| `tex_prefetch = 0` | Subidas de texturas adelantadas en un hilo aparte |
| `dump_key = 1` | No arregla nada: con el defecto en pantalla, F12 vuelca el fotograma (carpeta `dump` junto al ejecutable) con cada pase y cada textura; es el dato que identifica la operación rota |

Desde el PR de la segunda ronda, la línea `amd_diag:` del arranque deja escrito en
cada log qué combinación se probó.

## Evidencia del propietario (RX 6900 XT, runtime 0.6 real)

Copias locales en `build/user-reports/rx6900xt-0.6/` (no se suben):
`logs/newsnap.1cambieconfigs.log`, `logs/newsnap.nivel1tomefoto.log`,
`album-bands-0.6.webp`.

- Los dos logs son del runtime 0.6 (`snap_render`, `snap_supersample`,
  `snap_random_range`, proveedores FSR oficiales, `log: …/logs/newsnap.log`),
  controlador AMD 26.10.1 de la rama RDNA 1/2. Ya no es el runtime 0.1.x del
  informe `keyboard-after-photo.md`.
- Ambos terminan igual: `vk: device fault: "GPU fault"` con
  `write invalid at 0x…, precision 0x1000`. El controlador reporta una dirección de escritura GPU inválida con esa
  precisión; el mensaje no identifica por sí solo el recurso ni demuestra
  páginas host sin respaldo. No es una excepción de CPU.
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
   Coste: dos copias a staging por captura aceptada y estadísticas CPU tras el
   fence. Los PNG siguen saliendo solo con `NEWSNAP_PHOTO_TRACE_DIR`.
2. **Experimento de memoria opt-in:** `AC_SHADOW=1` (o `shadow = 1` en
   `newsnap.ini`) activa el almacenamiento shadow existente del donor;
   `AC_SHADOW=0` permite comparar las importaciones. Se retira la propuesta
   de activarlo automáticamente por vendor: no hay validación AMD ni medida
   controlada de coste que justifique cambiar todos sus pools.
3. El staging diagnóstico usa `vmaCreateBuffer` best-effort: si falla cualquiera
   de las dos asignaciones se libera lo ya reservado y se conserva la operación
   original. No llama a `vk_staging`, que termina el proceso ante un fallo.
   Un presupuesto atómico limita a **64 MiB de bytes solicitados de buffers
   diagnósticos pendientes**; se devuelve después de destruir los buffers en
   completion. No incluye overhead del allocator ni el buffer CPU temporal de
   estadísticas. Si se alcanza el presupuesto se omite esa captura sin consumir
   el límite de sesión. No se cambia la copia del juego.

## Pruebas ejecutadas

- `python -m unittest tests.test_photo_readback`: 3 OK. El fixture nativo cubre
  el modo solo-log, una banda parcial (`black_tiles16=0/7`, un tramo
  `y32:x16-127`) y el tope de capturas.
- Antes de las correcciones de revisión: runtime privado compilado con el kit 0.6
  (`build/foto01-build`): selftest y cargador del candidato OK.
- Ruta de fotos de 400 s en RTX 4060 con ese binario y sin ajustes
  (`build/foto01-newbin`): salida 0, cuatro pares de líneas, 0 bytes distintos,
  0 teselas negras.
- Ruta de fotos de 400 s en RTX 4060 con el 0.6 publicado y `AC_SHADOW=1`
  (`build/foto01-shadow1`): salida 0, fotos sin diferencias. Es el camino que
  el propietario puede probar explícitamente en AMD; no se activa por defecto.

### Correcciones de revisión CPU (sin nueva prueba GPU)

Se aplicó TDD sobre el código C generado real. La regresión falló inicialmente
con salida 21 al inyectar fallo en la primera asignación: se seguía usando la
ruta fatal. Después pasan los tres tests focalizados, incluyendo procesos nativos
separados que cubren fallo de primera/segunda asignación, cleanup parcial,
24 capturas sin archivos (la 25 no asigna ni graba comandos), límite de 64 MiB con
varias capturas sin completar y recuperación del presupuesto al terminar una. Ocho hilos ejercitan además 16.000 reservas/liberaciones del
presupuesto atómico sin sobrepasarlo ni dejar saldo pendiente.
Los fixtures anteriores de filas acolchadas, canales BGRA y bandas parciales
siguen pasando. Esto prueba propiedad y límites CPU; no ejecuta barreras GPU ni
valida el controlador AMD. El binario con estas últimas correcciones aún requiere
compilación e integración por el coordinador.

## Cómo leer el próximo log de la RX 6900 XT

| Línea `photo_trace: gpu-t2b` | Lectura |
|---|---|
| `mismatch_bytes=0` y `black_tiles16=0/0` | Las dos lecturas GPU coinciden; queda por verificar visibilidad CPU, writeback shadow, bytes que lee el juego y codificación/carga |
| `mismatch_bytes>0`, teselas negras solo en el buffer | Las lecturas de origen y destino GPU difieren; acota la ruta, pero no identifica importación, driver ni causa concreta |
| Teselas negras ya en el origen | El origen leído ya contiene negro; investigar producción/sincronización y comprobar que ese negro sea anómalo |

Prueba inmediata en la 0.6 ya instalada, sin binario nuevo: añadir `shadow = 1`
a `newsnap.ini` (o la variable de entorno `AC_SHADOW=1`) y repetir la foto del
primer nivel. Para separar FSR 4: repetir además con el escalador en FSR 3.1.

## Límites

- Nada de esto se ha ejecutado en AMD. El experimento shadow puede no cambiar nada.
- El modo shadow copia memoria por CPU en cada envío. En RTX la ruta mantuvo
  ≈60 fps de media; no se hizo comparación de rendimiento controlada y no hay
  medida en AMD.
- `shadow = 1` en `newsnap.ini` se aplica aunque el log lo anote como clave
  desconocida.
- El cierre de la sesión 1 no ocurrió al hacer una foto; no está demostrado que
  comparta causa con el de la sesión 2.
