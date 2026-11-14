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
Última entrega: [0.5.1-alpha publicada](https://github.com/MatyMeatBoy/NewSnapRecomp/releases/tag/v0.5.1-alpha).
La cola siguiente conserva únicamente investigación o aceptación pendientes.

## Tareas y reservas

**Coordinación inmediata: FOCO-01 está HECHA por confirmación del propietario
en RX 6900 XT. No seguir trabajando en el enfoque ni duplicar ese fix.** MatyMeatBoy
puede tomar **KEYBOARD-CRASH** (P0), continuar **FOTO-02** coordinando FOTO-01 o
tomar **HEAD-INTRO**. RTX tester lleva 404/kit local, autodetección de datos, Home y
consolas. La oscuridad/saturación sigue abierta; no cerrar COLOR-01 por el arreglo
del recuadro. Reporte completo: `docs/bugs/RX6900XT-REPORTES.md`.

| ID | Prioridad | Estado | Responsable | Trabajo y archivos reservados |
|---|---|---|---|---|
| RELEASE-06 | P0 | EN CURSO | RTX tester · 2026-11-14 | Petición: integrar MatyMeatBoy, continuar jugando y salir con 0.6. Plan docs/superpowers/plans/2026-11-14-v06.md. Root reserva integración adapt.py/version/build/paquete y GPU serial. No cerrar AMD/cabeza por cambio de versión ni modificar lógica/color. |
| DIAG-HISTORY-01 | P2 | REVISIÓN | RTX tester / mantenimiento · 2026-11-14 | Corregida omisión posterior a entrada256: scan inmediato completo, heaps constantes4logs/2observaciones, filtros antes de metadata. Quince pruebas (una omisión existente) y revisión independiente con órdenes/empates pasan. Sin borrar evidencia/recorrer datos; pendiente paquete0.6. docs/bugs/diagnostic-history.md. |
| POOL-BOUNDS-01 | P1 | REVISIÓN | RTX tester / investigación · 2026-11-14 | Condición de solapamiento reproducida en CPU. Logging limitado a 16 color + 4 DS y experimento AC_SNAP_POOL_BOUNDS=1 integrado, apagado por defecto. Cinco pruebas nativas/sintaxis/concurrencia pasan; no es fix AMD ni prueba de causa. Ver docs/bugs/pool-allocation-bounds.md. |
| HEAD-INTRO | P1 | REVISIÓN | MatyMeatBoy / RTX tester · PR #3 | PR y correcciones de revisión integrados: medida RTX de una toma, sin causa identificada ni fix. Intervención de timer concreta no cambia esa trayectoria; no descarta universalmente GPU/pacing/CRC. Tool conserva segmentos/paridad al descartar pares; diez tests y cuatro mediciones guardadas verificadas. Pendiente referencia comparable y JSON auditable de 30 FPS. docs/bugs/head-intro-stutter.md. |
| KEYBOARD-CRASH | P0 | REVISIÓN | MatyMeatBoy / integración RTX tester · PR #2 | PR integrado con bool exacto false, cuatro overrides de cuenta no fundamentados retirados y lectura de variante12bytes. Cuatro tests nativos/headerreal pasan. Se conserva triage nuevo de main y se acotan inferencias docs. Pendiente prueba integrada0.6/fotos/applet; cierre AMD no acreditado. docs/bugs/pr2-applet-contracts.md. |

| FOTO-01 | P0 | EN CURSO | RTX tester / captura GPU | REABIERTO: el propietario confirma fotos y miniaturas con bandas negras en RX 6900 XT usando el ZIP público 0.5. En otra pantalla de evaluación se ve una foto de Pikachu correcta; comparar rutas/slots y bytes, sin dar el JPEG por válido aún. Reservados adaptadores de color/readback y sus tests; hallazgo y capturas en `docs/bugs/RX6900XT-REPORTES.md`. |
| FOTO-02 | P0 | REVISIÓN | MatyMeatBoy · 2026-11-13 | **PR #1 revisado e integrado: los tres hallazgos están corregidos, 25 pruebas OK y límites de inferencia corregidos.** Validación con bytes AMD pendiente; ver `docs/bugs/photo-audit-review.md`. Resultado local: dos fotos NVIDIA únicas en bancos duplicados; sin bytes AMD que auditar aún. Auditoría CPU independiente de fotos guardadas: comprobar JPEG/bancos/CRC/dimensiones, determinar si las bandas están en bytes guardados o solo en preview. Archivos nuevos `tools/audit_saved_photos.py`, `tests/test_photo_audit.py`, informe `docs/bugs/photo-bands-cpu.md`. No modificar `saves.py`/`photos.py` sin coordinar. |
| TUTO-01 | P0 | EN CURSO | RTX tester / coordinación con MatyMeatBoy | El propietario pudo elegir carpetas de Pikachu/Vivillon y avanzar; después reportó teclado de Windows y cierre tras registro/evaluación de Pikachu. Ver KEYBOARD-CRASH. No cambiar lógica de sujetos/progreso ni recuperar el perfil anterior: recuperación excluida por el propietario. |
| INPUT-01 | P0 | REVISIÓN | RTX tester · 2026-11-13 | Cámara apunta sola: auditar mouse relativo, foco inicial, sticks y gyro; comprobar reposo, reconexión y cambio mando/ratón. Integrados `newsnap/camera_input_adapt.py` + `tests/test_camera_input.py`; 19 escenarios nativos y revisión independiente. Aceptación con mando/mouse físico pendiente. Sin activar sensores/vibración físicos por sorpresa. |
| GPU-WRITE-01 | P0 | REVISIÓN | RTX tester / agente de render | Draws gráficos con escrituras SSBO/imagen no pueden omitirse durante compilación. Fix específico integrado, 11 casos nativos y revisión independiente aprobados; compute ya era síncrono y queda descartado. `graphics_effects_adapt.py`, `tests/test_graphics_effects.py`, `docs/bugs/graphics-side-effects.md`. Binario integrado en prueba; causalidad AMD pendiente. |
| COLOR-01 | P0 | EN CURSO | RTX tester / renderer | REABIERTO en AMD: el propietario sigue viendo saturación excesiva con el ZIP público 0.5. Las nuevas capturas muestran HUD «AMD FSR 1, sharpness 80%»; comprobar runtime realmente iniciado al forzar lanzamiento, configuración efectiva y formato/transferencia. No bajar saturación arbitrariamente ni declarar equivalencia AMD por la prueba RTX. |
| PACE-01 | P1 | EN CURSO | RTX tester / agente de render | Puente entero con equivalencia completa y guardas de original/receta integrado; A/B local de dos pares inversos reduce p99 42,970→25,469 ms, conserva mediana ≈16,67 ms y aún registra pico 107,692 ms. Evidencia `build/v05-rng-pacing-ab/`; archivos `random_range_adapt.py`, `snap_random_range.*`, `test_random_range.py`, `cpu-asset-workers.md`. Aceptación final alpha RTX completada; AMD pendiente y virtual-core starvation sigue documentada, sin alterar prioridades/simulación. |
| PACE-CRC-01 | P2 | REVISIÓN | RTX tester / revisión CRC · 2026-11-14 | Restaurado por SHA e integrado; siete tests con2176casos/1024bytesCpu/8192bytesinput y revisión independiente de matemáticas/startup/CRC32C/deps pasan. Flag de opt-out conservado; rt_log registra selección. Pendiente build real y A/B mismoexe sin inferirFPS del micro. |
| PAD-01 | P1 | REVISIÓN | RTX tester / agente de controles | Backend SDL de prueba de mandos implementado y probado con dispositivos virtuales/ABI real. Reservados `controller_probe.py`, `controller_ui.py`, `tests/test_controller_probe.py`. UI visual se integra con ART-01. |
| VRR-01 | P1 | REVISIÓN | RTX tester / agente de render | Estado real de presentación por VK_EXT_present_timing, unknown/fixed/variable; nunca inferir VRR por FIFO/mailbox. Reservados `vrr_adapt.py`, overlays `snap_vrr*`, `display_status.py`, `display_ui.py`, tests y `docs/DISPLAY.md`. Prueba swapchain real integrada completada: API disponible, intervalo cero → unknown, sin inferir VRR. Validación FreeSync física pendiente. |
| MENU-01 | P1 | REVISIÓN | RTX tester / agente de render | Menú dentro del juego: Original/Auto/DLSS/FSR 3.1/FSR 4, Native AA/DLAA y tres presets reducidos. Quitar FSR 3 genérico, XeSS/FSR espacial y opciones artísticas ignoradas. Reservados `menu_adapt.py`, `tests/test_snap_menu.py`. |
| QA-AMD-01 | P0 | EN CURSO | RTX tester / propietario · RX 6900 XT | Prueba física iniciada sobre ZIP público 0.5. Recuadro de foto confirmado correcto; fotos/miniaturas y color fallan; cabeza vibra en intro; launcher falla y cierre tras teclado Windows. Registrar launcher/version/hash del runtime por separado, ya que hubo lanzamiento forzado. No declarar toda AMD validada. |

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
  `clipboard-473be5db-…`, `clipboard-b8af3c5e-…` en su Temp local.
  Copiar a `build/user-reports/` para inspección, sin añadirlas a Git.

## Referencia de ReKHCoM para ART-01

`D:/Dev/ReKHCoM-build/LEEME.md` señala como mapa canónico
`C:/Users/MP/Documents/00 MatyMeatBoy/KHCoMPC/LEEME.md` y `NOTES.md`.
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
