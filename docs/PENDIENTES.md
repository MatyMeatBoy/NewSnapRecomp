# Cola compartida: RTX tester + MatyMeatBoy

**Integración en `main`; entregas por PR temático.** Las ramas auxiliares
0.4/0.5 ya se integraron y eliminaron; no recrearlas. Preparar PR de MatyMeatBoy en
un worktree aislado, conservando el checkout compartido en `main`.
La release/tag `v0.4.0-alpha` permanece inmutable. Por petición posterior del
propietario se publicó **`v0.5.0-alpha` limitada**, sin declararla estable ni dar
por verificados los casos AMD/mando/FreeSync o los picos de pacing pendientes.
Las filas de aceptación física conservan su estado hasta disponer de evidencia.

Leer este archivo antes de tomar trabajo. Los responsables de la tabla tienen
reservados sus archivos; confirmar aquí un cambio de responsable antes de editar.
Para tomar una tarea libre, cambiar su estado a `EN CURSO`, escribir responsable,
fecha/hora y archivos reservados. Una tarea pasa a `REVISIÓN` con evidencia y
comandos, y a `HECHA` después de revisión independiente. No declarar una tarea
resuelta solo por cambiar un ajuste o por compilar.

## Reglas comunes

- Preservar partidas, fotos, imports y configuración del usuario. Pruebas solo
  sobre copias; `newsnapGameData` original queda en 0.4 para su prueba externa.
- Conservar la lógica del juego: no omitir evaluación de sujetos, saltar el
  tutorial, editar flags de progreso ni fabricar puntuaciones para ocultar bugs.
- Mantener color/posprocesado de Snap. Corregir transferencias de color erróneas;
  no compensarlas bajando saturación/contraste arbitrariamente.
- Evidencia del propietario: **RX 6900 XT**, modo **Original**, monitor FreeSync.
  Evidencia local de RTX tester: **RTX 4060**. Una prueba en una GPU no valida la otra.
- Las capturas del usuario y datos derivados quedan en `build/`, sin subir fotos,
  claves, NSO/RomFS, guardados ni ejecutables recompilados a GitHub.
- Coordinar una sola prueba GPU a la vez. Repetir mismo recorrido/resolución y
  estado de caché para comparar frametimes. Separar CPU/GPU/compilación/esperas.
- No sobrescribir trabajo de otro responsable. Evitar reformateos globales.
  Avisar a RTX tester antes de editar `launcher.py`, `adapt.py`, `build.py`,
  `maintenance.py`, `version.py` o el empaquetado: son puntos de integración.
- Cada autor puede commitear solo su reserva en su rama temática de PR. RTX tester
  revisa, prueba e integra en `main`, y coordina publicación/cambio de versión.
  No cambiar de rama en el checkout compartido ni mezclar trabajo ajeno.

Las tareas terminadas se conservan en [historial de trabajo completado](PENDIENTES-HECHOS.md).
Última entrega: [0.6.0-alpha publicada](https://github.com/MatyMeatBoy/NewSnapRecomp/releases/tag/v0.6.0-alpha).
La cola siguiente conserva únicamente investigación o aceptación pendientes.

## Tareas y reservas

**Coordinación inmediata: FOCO-01 está HECHA por confirmación del propietario
en RX 6900 XT; no duplicar ese fix.** MatyMeatBoy lleva FOTO-01 (bandas, cierres y
diagnóstico GPU); su PR6 ya está integrado con correcciones de revisión. FOTO-02, la herramienta de auditoría,
ya está en el historial. RTX tester integró PR4/5/6/7/8/9/10 y conserva pendiente el turno GPU
para su aceptación interactiva final. El propietario confirma que el primer nivel
0.6 ya no se ve oscuro y parece funcionar a60FPS; esa confirmación no cierra las
fotos ni constituye una validación completa AMD/VRR/mando. Reporte histórico:
`docs/bugs/RX6900XT-REPORTES.md`.

| ID | Prioridad | Estado | Responsable | Trabajo y archivos reservados |
|---|---|---|---|---|
| CPU-WORKER-07 | P2 | REVISIÓN | RTX tester / CPU · 2026-11-14 | Analizar operación de recursos main+5ec890 y latencias de virtual core ya medidas. Buscar coste de lifting reducible manteniendo Cpu/memoria/yields; sin cambiar prioridades/simulación ni pruebas GPU concurrentes. Prototipo privado probado con Cpu completo/trazas/alias/streams y controles negativos; especialización UINT32_MAX aumenta código O1/O2 sin ganancia medida. No se integra como optimización. Reserva liberada; queda medida comparable si surge un candidato útil. |
| LAUNCH-POSTBUILD-06 | P0 | REVISIÓN | RTX tester · PR4/5 integrados | Dos causas corregidas: marcador de shaders sin registros bloqueaba el primer inicio; --boot ejecutaba una sonda que salía0 en primera NVN. PR4/5 integrados, CI y regresiones rojo→verde/revisión independiente. Prueba congelada anterior reprodujo exactamente el cierre0; queda observar ventana/frames en modo interactivo con el congelado corregido, cuando el turno GPU de MatyMeatBoy termine. No modificar GameData original ni la release0.6 publicada. |
| POOL-BOUNDS-01 | P1 | REVISIÓN | RTX tester / investigación · 2026-11-14 | Condición de solapamiento reproducida en CPU. Logging limitado a 16 color + 4 DS y experimento AC_SNAP_POOL_BOUNDS=1 integrado, apagado por defecto. Cinco pruebas nativas/sintaxis/concurrencia pasan; no es fix AMD ni prueba de causa. Ver docs/bugs/pool-allocation-bounds.md. |
| HEAD-INTRO | P1 | REVISIÓN | MatyMeatBoy / RTX tester · PR #3 | PR y correcciones de revisión integrados: medida RTX de una toma, sin causa identificada ni fix. Intervención de timer concreta no cambia esa trayectoria; no descarta universalmente GPU/pacing/CRC. Tool conserva segmentos/paridad al descartar pares; diez tests y cuatro mediciones guardadas verificadas. Pendiente referencia comparable y JSON auditable de 30 FPS. docs/bugs/head-intro-stutter.md. |
| KEYBOARD-CRASH | P0 | REVISIÓN | MatyMeatBoy / integración RTX tester · PR #2 | PR integrado con bool exacto false, cuatro overrides de cuenta no fundamentados retirados y lectura de variante12bytes. Cuatro tests nativos/headerreal pasan. Se conserva triage nuevo de main y se acotan inferencias docs. Recorrido RTX540s por fotos/evaluación/primera expedición y60s del binario final pasan; causa del teclado/cierre AMD no acreditada. docs/bugs/pr2-applet-contracts.md. |

| RELEASE-07-TESTER | P0 | EN CURSO | MatyMeatBoy · 2026-11-14 · orden directa del propietario | Publicar `v0.7.0-tester` como prerelease de prueba con todo lo integrado en main, para depurar en la RX 6900 XT. Reservados por esta entrega: `newsnap/version.py`, `assets/windows-version.txt`, `tools/build_launcher.py` (incluye `tools/pruebas-amd/` en el paquete), `docs/releases/0.7-tester.md`. No corrige los fallos AMD; no sustituye a 0.6. Kit y ZIP desde `toolchain/newsnap-14patches-sdk` con el pin de traductor de main. |
| FOTO-01 | P0 | REVISIÓN | MatyMeatBoy / revisión RTX tester · PR #6 · 2026-11-14 | **Tercera ronda: causa encontrada y corregida en AMD.** El volcado F12 de la prueba 6 mostró que la miniatura es una BC1 2D que el juego codifica dibujando por vistas de bloques; el controlador RDNA 1/2 escribe fuera de esas imágenes (issue #5 del donor, ya evitado allí solo para BC 3D). `newsnap/bc_block_views_adapt.py`: `AC_BLOCK_VIEWS`, por defecto 0 en `vk_caps.amd_sc` (NVIDIA sin cambio), BC 2D por imagen intermedia refrescada por pase. Probado en la RX 6900 XT: miniatura completa, interfaz limpia, sin `write invalid` (una sesión). Pendiente: más niveles/álbum/cuadrados y control RTX con `AC_BLOCK_VIEWS=0`. Ver `docs/bugs/amd-photo-gpu-fault.md`. Reservados además `bc_block_views_adapt.py`, `test_bc_block_views.py`. — Historial: Dos logs 0.6 RX 6900 XT reportan write-invalid y fotos con bandas; causa no acreditada. Diagnóstico GPU→buffer siempre activo, PNG opt-in, asignación best-effort y presupuesto atómico de 64 MiB pendiente. Shadow permanece experimento AC_SHADOW=1 explícito, sin default por vendor ni aceptación AMD. Tests nativos: fallos de ambas asignaciones, cleanup parcial, límite de 24 sin PNG y presupuesto pendiente; PR6 integrado; runtime privado compila y pasa selftest/loader; entrega pública y prueba física pendientes. Nuevo log confirma shadow activo y el mismo tipo de fault, sin demostrar causa FSR4 ni estado de fotos. Ver docs/bugs/integration-07.md. No inferir visibilidad CPU/JPEG ni causa import/driver desde mismatch GPU. Reservados photo_readback_adapt.py, test_photo_readback.py, amd-photo-gpu-fault.md; evidencia privada build/foto01-*. **Segunda ronda del propietario (0.6, RX 6900 XT):** la miniatura de la foto ya sale con franjas dentro del nivel (patrón fijo, 1 de cada 4 tramos), también retrato del profesor, placa del nombre y marco; vuelven los cuadrados de GPU-WRITE-01; con `fifo` el retrato sale bien; shadow no cambia el aspecto. En RTX todo limpio; dentro del nivel la foto es un pase de dibujo sin copias. PR #11 (MatyMeatBoy): línea `amd_diag:` con los ajustes A/B en cada log y seis `.bat` de descarte en `tools/pruebas-amd/`; la combinación conservadora pasa la ruta de fotos en RTX. Pendiente del propietario: pruebas 1 a 6 en la RX 6900 XT. |
| TUTO-01 | P0 | EN CURSO | RTX tester / coordinación con MatyMeatBoy | El propietario pudo elegir carpetas de Pikachu/Vivillon y avanzar; después reportó teclado de Windows y cierre tras registro/evaluación de Pikachu. Ver KEYBOARD-CRASH. No cambiar lógica de sujetos/progreso ni recuperar el perfil anterior: recuperación excluida por el propietario. |
| INPUT-01 | P0 | REVISIÓN | RTX tester · 2026-11-13 | Cámara apunta sola: auditar mouse relativo, foco inicial, sticks y gyro; comprobar reposo, reconexión y cambio mando/ratón. Integrados `newsnap/camera_input_adapt.py` + `tests/test_camera_input.py`; 19 escenarios nativos y revisión independiente. Aceptación con mando/mouse físico pendiente. Sin activar sensores/vibración físicos por sorpresa. |
| GPU-WRITE-01 | P0 | REVISIÓN | RTX tester / agente de render | Draws gráficos con escrituras SSBO/imagen no pueden omitirse durante compilación. Fix específico integrado, 11 casos nativos y revisión independiente aprobados; compute ya era síncrono y queda descartado. `graphics_effects_adapt.py`, `tests/test_graphics_effects.py`, `docs/bugs/graphics-side-effects.md`. Binario integrado en prueba; causalidad AMD pendiente. |
| COLOR-01 | P0 | REVISIÓN | RTX tester / renderer | Actualización0.6: propietario confirma que el primer nivel ya no se ve oscuro en RX6900XT y parece funcionar bien a60FPS. Confirmación acotada a esa escena; no es benchmark ni cierra fotos, otros modos o saturación de todas las escenas. Reporte anterior: saturación excesiva con ZIP0.5. Las nuevas capturas muestran HUD «AMD FSR 1, sharpness 80%»; comprobar runtime realmente iniciado al forzar lanzamiento, configuración efectiva y formato/transferencia. No bajar saturación arbitrariamente ni declarar equivalencia AMD por la prueba RTX. |
| PACE-01 | P1 | EN CURSO | RTX tester / agente de render | Puente entero con equivalencia completa y guardas de original/receta integrado; A/B local de dos pares inversos reduce p99 42,970→25,469 ms, conserva mediana ≈16,67 ms y aún registra pico 107,692 ms. Evidencia `build/v05-rng-pacing-ab/`; archivos `random_range_adapt.py`, `snap_random_range.*`, `test_random_range.py`, `cpu-asset-workers.md`. Aceptación final alpha RTX completada; AMD pendiente y virtual-core starvation sigue documentada, sin alterar prioridades/simulación. |
| PAD-01 | P1 | REVISIÓN | RTX tester / agente de controles | Backend SDL de prueba de mandos implementado y probado con dispositivos virtuales/ABI real. Reservados `controller_probe.py`, `controller_ui.py`, `tests/test_controller_probe.py`. UI visual se integra con ART-01. |
| VRR-01 | P1 | REVISIÓN | RTX tester / agente de render | Estado real de presentación por VK_EXT_present_timing, unknown/fixed/variable; nunca inferir VRR por FIFO/mailbox. Reservados `vrr_adapt.py`, overlays `snap_vrr*`, `display_status.py`, `display_ui.py`, tests y `docs/DISPLAY.md`. Prueba swapchain real integrada completada: API disponible, intervalo cero → unknown, sin inferir VRR. Validación FreeSync física pendiente. |
| MENU-01 | P1 | REVISIÓN | RTX tester / agente de render | Menú dentro del juego: Original/Auto/DLSS/FSR 3.1/FSR 4, Native AA/DLAA y tres presets reducidos. Quitar FSR 3 genérico, XeSS/FSR espacial y opciones artísticas ignoradas. Reservados `menu_adapt.py`, `tests/test_snap_menu.py`. |
| QA-AMD-01 | P0 | EN CURSO | RTX tester / propietario · RX 6900 XT | Prueba física0.6 en curso: propietario confirma primer nivel sin oscuridad y funcionamiento aparente a60FPS. Fotos/miniaturas siguen corruptas y dos cierres actuales registran escritura GPU inválida. MatyMeatBoy trabaja en esos fallos. Evidencia histórica ZIP0.5: Recuadro de foto confirmado correcto; fotos/miniaturas y color fallan; cabeza vibra en intro; launcher falla y cierre tras teclado Windows. Registrar launcher/version/hash del runtime por separado, ya que hubo lanzamiento forzado. No declarar toda AMD validada. |

## Evidencia ya disponible (local, no subir)

- `build/v04-production-owner-maintenance/verification.json`: runtime 0.4 final,
  perfiles/configuración preservados; backup `build/runtime-backups/0.3-before-0.4`.
- `build/v04-production-neutral-fsr31/`: prueba del runtime portable final sobre
  copia de perfil; nunca confundirla con evidencia física AMD.
- `build/v05-original-color-chain/`: Original, captura de juego y presentación;
  `pixel-comparison-scaled.json` cuantifica error de transferencia de color.
- `build/v03-jump-fixed/`: tutorial, evaluación previa, primeras fotos válidas y
  ruta reproducible. `tests/routes/tutorial-photo.txt` conserva su script.
- Capturas del propietario: archivos `clipboard-4d415416-…`,
  `clipboard-473be5db-…`, `clipboard-b8af3c5e-…` en su carpeta temporal local.
  Copiar a `build/user-reports/` para inspección, sin añadirlas a Git.

## Referencia de ReKHCoM para ART-01

El `LEEME.md` de la carpeta local `ReKHCoM-build` señala como mapa canónico el
`LEEME.md` y el `NOTES.md` del proyecto local `KHCoMPC` del propietario.
No recorrer junctions ni duplicar hardlinks. Reutilizar solo el gráfico de mando
original solicitado por el propietario, adaptando sus etiquetas a Switch.

**Original localizado por RTX tester:** en el repositorio `khcom`, ref
`refs/heads/release/v2.9-20261106` (commit `51edf7efa2c49c97a1c389ae2e4cd7e3b749448c`),
`port/assets/controller/ultimate2c-sprite.png` (104×72 RGBA) y
`ultimate2c-transparent.png` (1254×1254). El checkout HEAD antiguo no los contiene.
`port/assets/controller/README.md` confirma que es el arte elegido por el usuario;
`port/src/port_controller_art.inc` tiene paleta/índices del sprite. Copias de
referencia local en `build/controller-reference-rekhcom/`, sin editar. SHA-256
del sprite: `a8daabc38680527ad0bb4cc3115b9b07e157b0ea4f00aac27d1d042536b103c4`.
ART-01 tomada por RTX tester para integrar el original localizado; no duplicar edición. Rejilla 104×72, paleta original y escala entera; UI nativa con etiquetas Switch.


## Puerta de aceptación completa, posterior a la alpha limitada

- Fotos y thumbnails correctos; selección/evaluación/relectura/exportación de
  fotos con sujetos claros; tutorial completado sin editar su lógica.
- Indicador de enfoque correcto en movimiento y zoom.
- Cámara estable en reposo y cambio de dispositivos; causa de vibración/pacing
  documentada y comparada con la misma escena.
- Color digital correcto y sin ajustes añadidos; validación por GPU registrada.
- Home/launcher y canales de actualización comprobados; opciones FSR coherentes.
- Pruebas automáticas, nativas, integración, revisión independiente y evidencias
  de hardware pendientes explícitas. Una tarea en REVISIÓN no cumple esta puerta.
