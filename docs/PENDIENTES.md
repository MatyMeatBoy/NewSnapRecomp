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

## Tareas y reservas

| ID | Prioridad | Estado | Responsable | Trabajo y archivos reservados |
|---|---|---|---|---|
| RELEASE-05 | P0 | HECHA | RTX tester · 2026-11-13 | `v0.5.0-alpha` publicada sobre `e314751d`, prerelease y fuera de Latest estable. Dos ZIP públicos + dos SHA256 remotos verificados; compilación real desde el kit y 540 s/fotos/tutorial del nuevo binario correctos, actualización/reparación/kit descargados de la release publicada. 0.4 intacta. Evidencia `docs/bugs/v05-alpha-acceptance.md`; AMD/mando/FreeSync mantienen pendientes. |
| FOTO-01 | P0 | REVISIÓN | RTX tester / agente de captura | Bandas negras en fotos y miniaturas; aislar captura GPU → readback → JPEG → textura de preview. Reservados `newsnap/color_transfer_adapt.py`, `tests/test_color_transfer.py`, `newsnap/photo_readback_adapt.py`, `tests/test_photo_readback.py`; coordinar seams del renderer. |
| FOTO-02 | P0 | REVISIÓN | MatyMeatBoy · 2026-11-13 | **PR #1 revisado e integrado: los tres hallazgos están corregidos, 25 pruebas OK y límites de inferencia corregidos.** Validación con bytes AMD pendiente; ver `docs/bugs/photo-audit-review.md`. Resultado local: dos fotos NVIDIA únicas en bancos duplicados; sin bytes AMD que auditar aún. Auditoría CPU independiente de fotos guardadas: comprobar JPEG/bancos/CRC/dimensiones, determinar si las bandas están en bytes guardados o solo en preview. Archivos nuevos `tools/audit_saved_photos.py`, `tests/test_photo_audit.py`, informe `docs/bugs/photo-bands-cpu.md`. No modificar `saves.py`/`photos.py` sin coordinar. |
| FOCO-01 | P0 | LIBRE · CLAUDE | Sin asignar | Indicador de enfoque corrupto que sigue a Pikachu en Original: identificar draw/shader/textura del HUD y proponer fix verificable. Reservar nuevo `newsnap/focus_adapt.py`, `tests/test_focus.py`; no tocar adaptadores de color/readback ajenos. |
| TUTO-01 | P0 | REVISIÓN | RTX tester / aceptación del propietario | El propietario atribuyó el apuntado involuntario a mouse/gyro y pidió no cambiar lógica. La alpha supera tutorial/evaluación y primera expedición en RTX con fotos nuevas válidas. Pendiente comprobar fotos nuevas y flujo normal en AMD. Por indicación posterior del propietario, recuperar el perfil anterior queda fuera del alcance y no es requisito de aceptación; ver `docs/bugs/v05-owner-validation.md`. |
| INPUT-01 | P0 | REVISIÓN | RTX tester · 2026-11-13 | Cámara apunta sola: auditar mouse relativo, foco inicial, sticks y gyro; comprobar reposo, reconexión y cambio mando/ratón. Integrados `newsnap/camera_input_adapt.py` + `tests/test_camera_input.py`; 19 escenarios nativos y revisión independiente. Aceptación con mando/mouse físico pendiente. Sin activar sensores/vibración físicos por sorpresa. |
| GPU-WRITE-01 | P0 | REVISIÓN | RTX tester / agente de render | Draws gráficos con escrituras SSBO/imagen no pueden omitirse durante compilación. Fix específico integrado, 11 casos nativos y revisión independiente aprobados; compute ya era síncrono y queda descartado. `graphics_effects_adapt.py`, `tests/test_graphics_effects.py`, `docs/bugs/graphics-side-effects.md`. Binario integrado en prueba; causalidad AMD pendiente. |
| COLOR-01 | P0 | REVISIÓN | RTX tester / agente de captura | Transferencia sRGB→UNORM causa oscurecimiento/contraste. Integrado y revisado; par digital 1920×1080 byteidéntico en RTX 4060, además de matriz nativa de formatos fuente/destino. Mismos archivos de color de FOTO-01. Validación AMD pendiente del propietario. |
| PACE-01 | P1 | EN CURSO | RTX tester / agente de render | Puente entero con equivalencia completa y guardas de original/receta integrado; A/B local de dos pares inversos reduce p99 42,970→25,469 ms, conserva mediana ≈16,67 ms y aún registra pico 107,692 ms. Evidencia `build/v05-rng-pacing-ab/`; archivos `random_range_adapt.py`, `snap_random_range.*`, `test_random_range.py`, `cpu-asset-workers.md`. Aceptación final alpha RTX completada; AMD pendiente y virtual-core starvation sigue documentada, sin alterar prioridades/simulación. |
| UI-01 | P0 | HECHA | RTX tester | Home: cargar/importar GameData, verificar datos, versión y lanzar. Iniciar expedición no navega a Actualizar. Aviso automático solo ante estable más nueva; manual admite latest/prereleases y reparación. Revisión y smoke real de instalación/reparación: `docs/bugs/launcher-home-review.md`; commit `590347d`. Reservados `launcher.py`, `update_ui.py`, `maintenance_ui.py`, `launcher_settings.py`, módulos nuevos Home/updates y sus tests. Paquete dev1 final verificado: 1103 archivos del manifiesto, arranque congelado con PATH mínimo y reparación de misma versión con sentinelas intactos; ver `docs/bugs/v05-dev1-acceptance.md`. |
| ART-01 | P1 | HECHA | RTX tester · 2026-11-13 | Localizar el mando pixelado ORIGINAL de ReKHCoM y adaptarlo a Switch (A derecha/B abajo/X arriba/Y izquierda, L/R/ZL/ZR/+/-/sticks). Referencia canónica indicada abajo. Salida `assets/controllers/` + procedencia; no copiar sprites del juego. Original 104×72 conservado por SHA, overlays nativos Switch y escala entera 4×; revisión visual `build/launcher-audit-v05/controller-switch-after.jpg`, pruebas de selección/desconexión. Sin activar sensores físicos. |
| PAD-01 | P1 | REVISIÓN | RTX tester / agente de controles | Backend SDL de prueba de mandos implementado y probado con dispositivos virtuales/ABI real. Reservados `controller_probe.py`, `controller_ui.py`, `tests/test_controller_probe.py`. UI visual se integra con ART-01. |
| VRR-01 | P1 | REVISIÓN | RTX tester / agente de render | Estado real de presentación por VK_EXT_present_timing, unknown/fixed/variable; nunca inferir VRR por FIFO/mailbox. Reservados `vrr_adapt.py`, overlays `snap_vrr*`, `display_status.py`, `display_ui.py`, tests y `docs/DISPLAY.md`. Prueba swapchain real integrada completada: API disponible, intervalo cero → unknown, sin inferir VRR. Validación FreeSync física pendiente. |
| MENU-01 | P1 | REVISIÓN | RTX tester / agente de render | Menú dentro del juego: Original/Auto/DLSS/FSR 3.1/FSR 4, Native AA/DLAA y tres presets reducidos. Quitar FSR 3 genérico, XeSS/FSR espacial y opciones artísticas ignoradas. Reservados `menu_adapt.py`, `tests/test_snap_menu.py`. |
| CACHE-01 | P2 | HECHA | RTX tester / agente de mantenimiento | Caché privada de C generado, con import/recipe/dependencias verificadas, límite y limpieza segura. Reservados `generation_cache.py`, `build.py`, `maintenance.py`, tests y `docs/GENERATION_CACHE.md`. Revisión independiente aprobada tras corregir identidad LZ4 y módulos inesperados; ensayo real `build/v05-generation-cache-real/evidence.json`: generación 86,820 s frente a restore 3,044 s + verificación 0,265 s, 150 archivos idénticos, sin reutilizar ejecutables. |
| QA-01 | P1 | HECHA | RTX tester · 2026-11-13 | Aceptación de la alpha publicada revisada independientemente: catálogo alpha manual, ningún aviso de stable inexistente, descarga y stage real, instalación/reparación de misma versión, 1103 hashes, tres sentinelas conservados, launcher con PATH limpio y kit exacto descargado/reutilizado offline. Compilación real del GameData 0.4 copiado comprobada por separado. Rechazos/cancelación cubiertos por suite de 299; ver `docs/bugs/v05-alpha-acceptance.md`. |
| QA-AMD-01 | P0 | REVISIÓN | RTX tester / aceptación del propietario · 2026-11-13 | `v0.5.0-alpha` publicada, productor `e314751d`, con launcher/kit exactos y reconstrucción local comprobada. Ensayo final RTX del nuevo binario correcto; RX 6900 XT/mando/FreeSync siguen sin aceptación física. El dev1 privado anterior permanece inmutable. Protocolo `docs/bugs/v05-owner-validation.md`; no modificar originales para la prueba. |
| KIT-ALPHA-01 | P0 | HECHA | RTX tester / revisor de mantenimiento · 2026-11-13 | Adquisición del kit alpha/dev exacto de la versión instalada corregida y revisada; regresión rojo→verde, 30 pruebas específicas y suite completa de 299. Mantiene tag/revisión/assets/hashes/inventario y rechazo de drafts/versiones ajenas. Los avisos automáticos siguen solo stable. Archivos `newsnap/build_kit.py`, `tests/test_build_kit.py`. |
| LEARN-01 | P2 | HECHA | RTX tester · 2026-11-13 | Consolidar lecciones verificadas para OptiPort y matriz AMD/NVIDIA. Crear `docs/bugs/GPU_MATRIX.md`; separar observado/inferido/corregido/validado por GPU. Revisado y promovido a OptiPort `9673006`; siete referencias instaladas en RTX tester, checkout activo y cambios locales de MatyMeatBoy preservados. Evidencia/matriz en `docs/bugs/GPU_MATRIX.md`. |

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
