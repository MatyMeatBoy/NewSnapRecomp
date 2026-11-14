# Cola compartida: Codex + Claude

**Integración en `main`; entregas por PR temático.** Las ramas auxiliares
0.4/0.5 ya se integraron y eliminaron; no recrearlas. Preparar PR de Claude en
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
  Evidencia local de Codex: **RTX 4060**. Una prueba en una GPU no valida la otra.
- Las capturas del usuario y datos derivados quedan en `build/`, sin subir fotos,
  claves, NSO/RomFS, guardados ni ejecutables recompilados a GitHub.
- Coordinar una sola prueba GPU a la vez. Repetir mismo recorrido/resolución y
  estado de caché para comparar frametimes. Separar CPU/GPU/compilación/esperas.
- No sobrescribir trabajo de otro responsable. Evitar reformateos globales.
  Avisar a Codex antes de editar `launcher.py`, `adapt.py`, `build.py`,
  `maintenance.py`, `version.py` o el empaquetado: son puntos de integración.
- Cada autor puede commitear solo su reserva en su rama temática de PR. Codex
  revisa, prueba e integra en `main`, y coordina publicación/cambio de versión.
  No cambiar de rama en el checkout compartido ni mezclar trabajo ajeno.

## Tareas y reservas

**Coordinación inmediata: FOCO-01 está HECHA por confirmación del propietario
en RX 6900 XT. No seguir trabajando en el enfoque ni duplicar ese fix.** Claude
puede tomar **KEYBOARD-CRASH** (P0), continuar **FOTO-02** coordinando FOTO-01 o
tomar **HEAD-INTRO**. Codex lleva 404/kit local, autodetección de datos, Home y
consolas. La oscuridad/saturación sigue abierta; no cerrar COLOR-01 por el arreglo
del recuadro. Reporte completo: `docs/bugs/RX6900XT-REPORTES.md`.

| ID | Prioridad | Estado | Responsable | Trabajo y archivos reservados |
|---|---|---|---|---|
| UI-TECH-01 | P1 | REVISIÓN | Codex | Implementados nombres Vulkan/AF/frame cap/prebuffer, tooltips de opciones y presets Original/Bajo/Medio/Alto/Ultra explícitos; manual cambia a Personalizado. Revisión independiente y Tk real pasan; FPS/presentación/color permanecen independientes. Modo solicitado y efectivo separados; desconocido VRR no se presenta como activo. Fuente pendiente de freeze/entrega. |
| BRAND-01 | P1 | REVISIÓN | Codex | Implementados newsnap.log/newsnap.N.log/newsnap.ini y avisos visibles NewSnap, con 49 anclas y pruebas nativas de rotación/config. Lectura legacy solo si nuevo ausente; primer guardado conserva líneas y nunca escribe el antiguo. Licencias y logs previos intactos. Aplicación conjunta de overlays pasa; falta nuevo binario. Ver docs/bugs/runtime-branding.md. |
| DIAG-01 | P1 | REVISIÓN | Codex | Botón Exportar diagnóstico y backend local acotado implementados. ZIP con identidad/hash/ajustes/logs/observaciones históricas; excluye juego, fotos, partidas y credenciales. Revisión corrigió rutas privadas con espacios y soporte USB/exFAT; 11 pruebas dirigidas, una omitida por privilegio symlink (reparse attribute cubierto). Pendiente freeze/entrega. |
| LAUNCH-404 | P0 | REVISIÓN | Codex · 47be383 | Corregido en fuente: paquete Windows incluye kit exacto fijado por hash/tamaño y cliente lo verifica sin red; 404 remoto explica falta de acceso al repo privado. Revisión independiente sin bloqueos nuevos, 72 pruebas dirigidas pasan. Falta freeze/entrega y validación del paquete completo sin credenciales; ZIP publicado sigue inmutable. Evidencia `docs/bugs/launcher-portable-corrections.md`. |
| AUTO-DATA | P0 | REVISIÓN | Codex · 47be383 | Detección acotada prioriza imports completos sobre preferencias ausentes/marker-only, soporta layouts directos/anidados/vecinos y no modifica preferencias. Guardada regresión de instalación inexistente. Pruebas de rutas/estado/mantenimiento pasan; pendiente aceptación del nuevo paquete en otro PC. Ver `docs/bugs/launcher-portable-corrections.md`. |
| HOME-PROFILE | P1 | REVISIÓN | Codex | Selector retirado de Inicio y movido a Opciones → Juego; modelo/perfil preservado y busy deshabilita selector. Comprobado con jerarquía Tk real y callbacks; falta entregar el nuevo EXE. |
| CONSOLE-01 | P1 | REVISIÓN | Codex · 47be383 | Wrappers Python/Ninja y helpers nativos ocultos al salir del launcher, preservando consola CLI explícita, pipes/exit/Job/cancelación. Pruebas nativas/cleanup y aplicación conjunta de overlays pasan; pendiente binario nuevo y aceptación visual externa. No cerrar CMD ajenos. Ver `docs/bugs/launcher-portable-corrections.md`. |
| HEAD-INTRO | P1 | EN CURSO | Claude · 2026-11-13 | Solo la cabeza del personaje parece stutterear cuando entra caminando en la intro antes del logo. Comparar actualización/animación de cabeza y cuerpo, distinguir pasos de animación de picos de frame o cámara. No asumir que lo causa CRC ni modificar simulación 30/60. Reservar adaptador/test nuevos y documentar caso/ruta/evidencia. |
| KEYBOARD-CRASH | P0 | REVISIÓN | Claude / revisión Codex · PR #2 | Log AMD: fatal `rt_dispatch sdk+0x273060` compatible con defecto JPEG/longjmp antiguo; generación inferida por parches/log, sin hash del ejecutable. No se identificó qué abrió el teclado de Windows. PR recibido y CI pasa, pero overlay requiere corregir retorno bool de HandleNetworkRequestErrorResult (622→false) y justificar códigos sintéticos de cuenta: callers distinguen descripciones. No mergear applets tal cual ni cerrar casos AMD. Hallazgos `docs/bugs/pr2-review.md`; Claude conserva esta ruta, Codex no duplica su repro. |

| RELEASE-05 | P0 | HECHA | Codex · 2026-11-13 | `v0.5.0-alpha` publicada sobre `e314751d`, prerelease y fuera de Latest estable. Dos ZIP públicos + dos SHA256 remotos verificados; compilación real desde el kit y 540 s/fotos/tutorial del nuevo binario correctos, actualización/reparación/kit descargados de la release publicada. 0.4 intacta. Evidencia `docs/bugs/v05-alpha-acceptance.md`; AMD/mando/FreeSync mantienen pendientes. |
| FOTO-01 | P0 | EN CURSO | Codex / captura GPU | REABIERTO: el propietario confirma fotos y miniaturas con bandas negras en RX 6900 XT usando el ZIP público 0.5. En otra pantalla de evaluación se ve una foto de Pikachu correcta; comparar rutas/slots y bytes, sin dar el JPEG por válido aún. Reservados adaptadores de color/readback y sus tests; hallazgo y capturas en `docs/bugs/RX6900XT-REPORTES.md`. |
| FOTO-02 | P0 | REVISIÓN | Claude · 2026-11-13 | **PR #1 revisado e integrado: los tres hallazgos están corregidos, 25 pruebas OK y límites de inferencia corregidos.** Validación con bytes AMD pendiente; ver `docs/bugs/photo-audit-review.md`. Resultado local: dos fotos NVIDIA únicas en bancos duplicados; sin bytes AMD que auditar aún. Auditoría CPU independiente de fotos guardadas: comprobar JPEG/bancos/CRC/dimensiones, determinar si las bandas están en bytes guardados o solo en preview. Archivos nuevos `tools/audit_saved_photos.py`, `tests/test_photo_audit.py`, informe `docs/bugs/photo-bands-cpu.md`. No modificar `saves.py`/`photos.py` sin coordinar. |
| FOCO-01 | P0 | HECHA | Confirmación del propietario · RX 6900 XT | El propietario confirma «el cuadrado de foto se ve bien ahora en 6900xt». Cierra ese defecto visual reportado; no cierra fotos guardadas, color, crash ni todas las variantes de zoom/HUD. No atribuir una causa concreta sin traza. |
| TUTO-01 | P0 | EN CURSO | Codex / coordinación con Claude | El propietario pudo elegir carpetas de Pikachu/Vivillon y avanzar; después reportó teclado de Windows y cierre tras registro/evaluación de Pikachu. Ver KEYBOARD-CRASH. No cambiar lógica de sujetos/progreso ni recuperar el perfil anterior: recuperación excluida por el propietario. |
| INPUT-01 | P0 | REVISIÓN | Codex · 2026-11-13 | Cámara apunta sola: auditar mouse relativo, foco inicial, sticks y gyro; comprobar reposo, reconexión y cambio mando/ratón. Integrados `newsnap/camera_input_adapt.py` + `tests/test_camera_input.py`; 19 escenarios nativos y revisión independiente. Aceptación con mando/mouse físico pendiente. Sin activar sensores/vibración físicos por sorpresa. |
| GPU-WRITE-01 | P0 | REVISIÓN | Codex / agente de render | Draws gráficos con escrituras SSBO/imagen no pueden omitirse durante compilación. Fix específico integrado, 11 casos nativos y revisión independiente aprobados; compute ya era síncrono y queda descartado. `graphics_effects_adapt.py`, `tests/test_graphics_effects.py`, `docs/bugs/graphics-side-effects.md`. Binario integrado en prueba; causalidad AMD pendiente. |
| COLOR-01 | P0 | EN CURSO | Codex / renderer | REABIERTO en AMD: el propietario sigue viendo saturación excesiva con el ZIP público 0.5. Las nuevas capturas muestran HUD «AMD FSR 1, sharpness 80%»; comprobar runtime realmente iniciado al forzar lanzamiento, configuración efectiva y formato/transferencia. No bajar saturación arbitrariamente ni declarar equivalencia AMD por la prueba RTX. |
| PACE-01 | P1 | EN CURSO | Codex / agente de render | Puente entero con equivalencia completa y guardas de original/receta integrado; A/B local de dos pares inversos reduce p99 42,970→25,469 ms, conserva mediana ≈16,67 ms y aún registra pico 107,692 ms. Evidencia `build/v05-rng-pacing-ab/`; archivos `random_range_adapt.py`, `snap_random_range.*`, `test_random_range.py`, `cpu-asset-workers.md`. Aceptación final alpha RTX completada; AMD pendiente y virtual-core starvation sigue documentada, sin alterar prioridades/simulación. |
| PACE-CRC-01 | P2 | REVISIÓN | Codex / implementador CRC | Prototipo CPU listo: siete tests y oráculo completo pasan; micro mejora 4,39x O1, sin prueba de FPS. Integración aplazada por bloqueos de launcher/fotos/crash AMD. Mantener fuera de la entrega correctiva hasta revisión; reserva de fuentes `snap_crc*` y helper/test/generador CRC. Plan `docs/superpowers/plans/2026-11-13-crc-isa.md`. |
| UI-01 | P0 | EN CURSO | Codex | REABIERTO por fallos reales del propietario en RX 6900 XT/ZIP público 0.5: 404 al correr, GameData vecina no detectada, consola persistente y selector de perfil que debe salir de Home. Ver LAUNCH-404, AUTO-DATA, HOME-PROFILE y CONSOLE-01. Pruebas locales previas no cierran estos reportes. |
| ART-01 | P1 | HECHA | Codex · 2026-11-13 | Localizar el mando pixelado ORIGINAL de ReKHCoM y adaptarlo a Switch (A derecha/B abajo/X arriba/Y izquierda, L/R/ZL/ZR/+/-/sticks). Referencia canónica indicada abajo. Salida `assets/controllers/` + procedencia; no copiar sprites del juego. Original 104×72 conservado por SHA, overlays nativos Switch y escala entera 4×; revisión visual `build/launcher-audit-v05/controller-switch-after.jpg`, pruebas de selección/desconexión. Sin activar sensores físicos. |
| PAD-01 | P1 | REVISIÓN | Codex / agente de controles | Backend SDL de prueba de mandos implementado y probado con dispositivos virtuales/ABI real. Reservados `controller_probe.py`, `controller_ui.py`, `tests/test_controller_probe.py`. UI visual se integra con ART-01. |
| VRR-01 | P1 | REVISIÓN | Codex / agente de render | Estado real de presentación por VK_EXT_present_timing, unknown/fixed/variable; nunca inferir VRR por FIFO/mailbox. Reservados `vrr_adapt.py`, overlays `snap_vrr*`, `display_status.py`, `display_ui.py`, tests y `docs/DISPLAY.md`. Prueba swapchain real integrada completada: API disponible, intervalo cero → unknown, sin inferir VRR. Validación FreeSync física pendiente. |
| MENU-01 | P1 | REVISIÓN | Codex / agente de render | Menú dentro del juego: Original/Auto/DLSS/FSR 3.1/FSR 4, Native AA/DLAA y tres presets reducidos. Quitar FSR 3 genérico, XeSS/FSR espacial y opciones artísticas ignoradas. Reservados `menu_adapt.py`, `tests/test_snap_menu.py`. |
| CACHE-01 | P2 | HECHA | Codex / agente de mantenimiento | Caché privada de C generado, con import/recipe/dependencias verificadas, límite y limpieza segura. Reservados `generation_cache.py`, `build.py`, `maintenance.py`, tests y `docs/GENERATION_CACHE.md`. Revisión independiente aprobada tras corregir identidad LZ4 y módulos inesperados; ensayo real `build/v05-generation-cache-real/evidence.json`: generación 86,820 s frente a restore 3,044 s + verificación 0,265 s, 150 archivos idénticos, sin reutilizar ejecutables. |
| QA-01 | P1 | HECHA | Codex · 2026-11-13 | Aceptación de la alpha publicada revisada independientemente: catálogo alpha manual, ningún aviso de stable inexistente, descarga y stage real, instalación/reparación de misma versión, 1103 hashes, tres sentinelas conservados, launcher con PATH limpio y kit exacto descargado/reutilizado offline. Compilación real del GameData 0.4 copiado comprobada por separado. Rechazos/cancelación cubiertos por suite de 299; ver `docs/bugs/v05-alpha-acceptance.md`. |
| QA-AMD-01 | P0 | EN CURSO | Codex / propietario · RX 6900 XT | Prueba física iniciada sobre ZIP público 0.5. Recuadro de foto confirmado correcto; fotos/miniaturas y color fallan; cabeza vibra en intro; launcher falla y cierre tras teclado Windows. Registrar launcher/version/hash del runtime por separado, ya que hubo lanzamiento forzado. No declarar toda AMD validada. |
| KIT-ALPHA-01 | P0 | HECHA | Codex / revisor de mantenimiento · 2026-11-13 | Adquisición del kit alpha/dev exacto de la versión instalada corregida y revisada; regresión rojo→verde, 30 pruebas específicas y suite completa de 299. Mantiene tag/revisión/assets/hashes/inventario y rechazo de drafts/versiones ajenas. Los avisos automáticos siguen solo stable. Archivos `newsnap/build_kit.py`, `tests/test_build_kit.py`. |
| LEARN-01 | P2 | HECHA | Codex · 2026-11-13 | Consolidar lecciones verificadas para OptiPort y matriz AMD/NVIDIA. Crear `docs/bugs/GPU_MATRIX.md`; separar observado/inferido/corregido/validado por GPU. Revisado y promovido a OptiPort `9673006`; siete referencias instaladas en Codex, checkout activo y cambios locales de Claude preservados. Evidencia/matriz en `docs/bugs/GPU_MATRIX.md`. |

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
ART-01 tomada por Codex para integrar el original localizado; no duplicar edición. Rejilla 104×72, paleta original y escala entera; UI nativa con etiquetas Switch.


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
