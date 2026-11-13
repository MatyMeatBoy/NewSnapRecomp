# Cola compartida: Codex + Claude

**Rama única: `main`.** Las ramas auxiliares 0.4/0.5 ya se integraron y eliminaron.
La release/tag `v0.4.0-alpha` permanece inmutable. La 0.5 está en desarrollo y
**no se publica hasta resolver y validar todos los fallos reportados**.

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
  Evidencia local de Codex: **RTX 4060**. Una prueba en una GPU no valida la otra.
- Las capturas del usuario y datos derivados quedan en `build/`, sin subir fotos,
  claves, NSO/RomFS, guardados ni ejecutables recompilados a GitHub.
- Coordinar una sola prueba GPU a la vez. Repetir mismo recorrido/resolución y
  estado de caché para comparar frametimes. Separar CPU/GPU/compilación/esperas.
- No sobrescribir trabajo de otro responsable. Evitar reformateos globales.
  Avisar a Codex antes de editar `launcher.py`, `adapt.py`, `build.py`,
  `maintenance.py`, `version.py` o el empaquetado: son puntos de integración.
- Commits/merge/publicación y cambio de versión los coordina Codex. No crear
  nuevas ramas por cuenta propia en esta sesión compartida.

## Tareas y reservas

| ID | Prioridad | Estado | Responsable | Trabajo y archivos reservados |
|---|---|---|---|---|
| FOTO-01 | P0 | EN CURSO | Codex / agente de captura | Bandas negras en fotos y miniaturas; aislar captura GPU → readback → JPEG → textura de preview. Reservados `newsnap/color_transfer_adapt.py`, `tests/test_color_transfer.py`, `newsnap/photo_readback_adapt.py`, `tests/test_photo_readback.py`; coordinar seams del renderer. |
| FOTO-02 | P0 | REVISIÓN | Claude · 2026-11-13 | **REVISIÓN: cambios requeridos en `docs/bugs/photo-audit-review.md` (sobrescritura de entrada, JPEG malformado y falso veredicto limpio).** Resultado local: dos fotos NVIDIA únicas en bancos duplicados; sin bytes AMD que auditar aún. Auditoría CPU independiente de fotos guardadas: comprobar JPEG/bancos/CRC/dimensiones, determinar si las bandas están en bytes guardados o solo en preview. Archivos nuevos `tools/audit_saved_photos.py`, `tests/test_photo_audit.py`, informe `docs/bugs/photo-bands-cpu.md`. No modificar `saves.py`/`photos.py` sin coordinar. |
| FOCO-01 | P0 | LIBRE · CLAUDE | Sin asignar | Indicador de enfoque corrupto que sigue a Pikachu en Original: identificar draw/shader/textura del HUD y proponer fix verificable. Reservar nuevo `newsnap/focus_adapt.py`, `tests/test_focus.py`; no tocar adaptadores de color/readback ajenos. |
| TUTO-01 | P0 | LIBRE · CLAUDE | Sin asignar | Reproducir softlock con dos fotos sin sujeto claro y documentar recuperación por flujo/guardado original. Crear ruta reproducible y pruebas/evidencia en `build/`; informe `docs/bugs/tutorial-photo-softlock.md`. No cambiar lógica ni partidas originales. Depende de FOTO-01/02 para cierre. |
| INPUT-01 | P0 | EN CURSO | Codex · 2026-11-13 | Cámara apunta sola: auditar mouse relativo, foco inicial, sticks y gyro; comprobar reposo, reconexión y cambio mando/ratón. Crear `newsnap/camera_input_adapt.py` + `tests/test_camera_input.py`; coordinar seams de `input*.c`. Sin activar sensores/vibración físicos por sorpresa. |
| COLOR-01 | P0 | EN CURSO | Codex / agente de captura | Transferencia sRGB→UNORM causa oscurecimiento/contraste. Ya hay comparación cuantitativa local y fixture nativo; falta integrar y probar salida corregida. Mismos archivos de color de FOTO-01. Validación AMD pendiente del propietario. |
| PACE-01 | P1 | EN CURSO | Codex / agente de render | Atribuir picos y regularidad en Original con cachés calientes. Medir p50/p95/p99 y tiempos xlate/pipeline/texture/fence/pacing. No cambiar simulación 30/60 ni desactivar async como parche final sin prueba causal. Posibles archivos nuevos `newsnap/pacing_adapt.py`, `tests/test_pacing.py`. |
| UI-01 | P0 | EN CURSO | Codex | Home: cargar/importar GameData, verificar datos, versión y lanzar. Iniciar expedición no navega a Actualizar. Aviso automático solo ante estable más nueva; manual admite latest/prereleases y reparación. Reservados `launcher.py`, `update_ui.py`, `maintenance_ui.py`, `launcher_settings.py`, módulos nuevos Home/updates y sus tests. |
| ART-01 | P1 | LIBRE · CLAUDE | Sin asignar | Localizar el mando pixelado ORIGINAL de ReKHCoM y adaptarlo a Switch (A derecha/B abajo/X arriba/Y izquierda, L/R/ZL/ZR/+/-/sticks). Referencia canónica indicada abajo. Salida `assets/controllers/` + procedencia; no copiar sprites del juego. Acordar dimensiones con Codex tras inspeccionar el original. |
| PAD-01 | P1 | REVISIÓN | Codex / agente de controles | Backend SDL de prueba de mandos implementado y probado con dispositivos virtuales/ABI real. Reservados `controller_probe.py`, `controller_ui.py`, `tests/test_controller_probe.py`. UI visual se integra con ART-01. |
| VRR-01 | P1 | REVISIÓN | Codex / agente de render | Estado real de presentación por VK_EXT_present_timing, unknown/fixed/variable; nunca inferir VRR por FIFO/mailbox. Reservados `vrr_adapt.py`, overlays `snap_vrr*`, `display_status.py`, `display_ui.py`, tests y `docs/DISPLAY.md`. Falta prueba swapchain real integrada. |
| MENU-01 | P1 | REVISIÓN | Codex / agente de render | Menú dentro del juego: Original/Auto/DLSS/FSR 3.1/FSR 4, Native AA/DLAA y tres presets reducidos. Quitar FSR 3 genérico, XeSS/FSR espacial y opciones artísticas ignoradas. Reservados `menu_adapt.py`, `tests/test_snap_menu.py`. |
| CACHE-01 | P2 | HECHA | Codex / agente de mantenimiento | Caché privada de C generado, con import/recipe/dependencias verificadas, límite y limpieza segura. Reservados `generation_cache.py`, `build.py`, `maintenance.py`, tests y `docs/GENERATION_CACHE.md`. Revisión independiente aprobada tras corregir identidad LZ4 y módulos inesperados; ensayo real `build/v05-generation-cache-real/evidence.json`: generación 86,820 s frente a restore 3,044 s + verificación 0,265 s, 150 archivos idénticos, sin reutilizar ejecutables. |
| QA-01 | P1 | LIBRE · CLAUDE | Sin asignar | Auditar updater/launcher sin editar integración: escenarios 0.4→0.5, misma versión, sin estable, manual alpha/latest, GameData antiguo y cancelación. Agregar tests en nuevo `tests/test_launcher_acceptance.py` y hallazgos `docs/bugs/launcher-acceptance.md`. Coordinar APIs con Codex. |
| LEARN-01 | P2 | LIBRE · CLAUDE | Sin asignar | Consolidar lecciones verificadas para OptiPort y matriz AMD/NVIDIA. Crear `docs/bugs/GPU_MATRIX.md`; separar observado/inferido/corregido/validado por GPU. No publicar ni editar la skill global hasta revisión de Codex. |

## Evidencia ya disponible (local, no subir)

- `build/v04-production-owner-maintenance/verification.json`: runtime 0.4 final,
  perfiles/configuración preservados; backup `build/runtime-backups/0.3-before-0.4`.
- `build/v04-production-neutral-fsr31/`: prueba del runtime portable final sobre
  copia de perfil; nunca confundirla con evidencia física AMD.
- `build/v05-original-color-chain/`: Original, captura de juego y presentación;
  `pixel-comparison-scaled.json` cuantifica error de transferencia de color.
- `build/v03-jump-fixed/`: tutorial, evaluación previa, primeras fotos válidas y
  ruta reproducible. `tests/routes/tutorial-photo.txt` conserva su script.
- Capturas del propietario: archivos `codex-clipboard-4d415416-…`,
  `codex-clipboard-473be5db-…`, `codex-clipboard-b8af3c5e-…` en su Temp local.
  Copiar a `build/user-reports/` para inspección, sin añadirlas a Git.

## Referencia de ReKHCoM para ART-01

`D:/01Claude/ReKHCoM-build/LEEME.md` señala como mapa canónico
`C:/Users/MP/Documents/00 Claude/KHCoMPC/LEEME.md` y `CLAUDE.md`.
No recorrer junctions ni duplicar hardlinks. Reutilizar solo el gráfico de mando
original solicitado por el propietario, adaptando sus etiquetas a Switch.

**Original localizado por Codex:** en el repositorio `khcom`, ref
`refs/heads/release/v2.9-20261106` (commit `51edf7efa2c49c97a1c389ae2e4cd7e3b749448c`),
`port/assets/controller/ultimate2c-sprite.png` (104×72 RGBA) y
`ultimate2c-transparent.png` (1254×1254). El checkout HEAD antiguo no los contiene.
`port/assets/controller/README.md` confirma que es el arte elegido por el usuario;
`port/src/port_controller_art.inc` tiene paleta/índices del sprite. Copias de
referencia local en `build/controller-reference-rekhcom/`, sin editar. SHA-256
del sprite: `a8daabc38680527ad0bb4cc3115b9b07e157b0ea4f00aac27d1d042536b103c4`.
ART-01 sigue libre para Claude; ya puede trabajar sobre el original localizado.


## Puerta de salida 0.5

- Fotos y thumbnails correctos; selección/evaluación/relectura/exportación de
  fotos con sujetos claros; tutorial completado sin editar su lógica.
- Indicador de enfoque correcto en movimiento y zoom.
- Cámara estable en reposo y cambio de dispositivos; causa de vibración/pacing
  documentada y comparada con la misma escena.
- Color digital correcto y sin ajustes añadidos; validación por GPU registrada.
- Home/launcher y canales de actualización comprobados; opciones FSR coherentes.
- Pruebas automáticas, nativas, integración, revisión independiente y evidencias
  de hardware pendientes explícitas. Una tarea en REVISIÓN no cumple esta puerta.
