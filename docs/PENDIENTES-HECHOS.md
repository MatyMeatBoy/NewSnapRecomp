# Trabajo completado y evidencia

Historial movido desde la cola activa el 14/11/2026. HECHA describe el alcance
indicado en cada fila, no una validación universal de GPU o del juego.

| ID | Prioridad | Estado | Responsable | Evidencia y alcance |
|---|---|---|---|---|
| VIDEO-UNIFIED-07 | P1 | HECHA | Codex · PR10 integrado | Todas las opciones de vídeo en una sola superficie desplazable; sin Básico/Avanzado. Nueve opciones, once comboboxes totales, tooltips, presets, presentación y callbacks preservados. Tk oculto/roundtrip y revisión AST independiente pasan; CI verde. Nueva entrega pública pendiente, sin aceptación visual interactiva nueva. docs/bugs/integration-07.md. |
| XLATE-SEMANTICS-07 | P1 | HECHA | Codex · PR9 integrado | BFE/BFI/SHF definidos, 14parches exactos preservando los12previos. 917440casos de métodos reales y18SPIRV sintéticos validados desde managed/NativeAOT; pin SHA/id y gates de build/copia/kit. Revisión independiente, CI y suite Windows465tests/1skip pasan. Runtime privado compila y pasa probes; kit público y AMD/gameplay pendientes. No acredita causa de fotos. docs/bugs/xlate-semantics.md. |
| CACHE-VERIFY-07 | P1 | HECHA | Codex · PR7 integrado | Verificación de hashes/artefactos y ausencia real de cinco rutas de caché antes de commit; rollback probado ante borrado silencioso y corrupción. Restauración validada antes de descartar backup; copia rechaza junctions anidados, limpieza de temporales comprobada y recibo visible/log. 79 tests focalizados (2 skips privados), revisión independiente aprobada y CI verde. No acredita causa de fotos AMD. docs/bugs/runtime-replacement-verification.md. |
| AMD-RESEARCH-07 | P1 | HECHA | Codex · PR8 integrado | Auditorías primarias de ports nativos y familias de emulación Switch1/2, con commits/merge/revert/hardware y aplicabilidad real; revisión independiente. Separan fixes ya presentes, candidatos y experimentos. Vida útil diferida queda como candidato FOTO-01 y bitfields/SHF en XLATE-SEMANTICS-07. Sin mejora FPS ni aceptación AMD inferida. docs/bugs/amd-native-source-audit.md y amd-emulation-source-audit.md. |
| UI-PROGRESS-06 | P1 | HECHA | Codex · PR4 integrado | Progreso estructurado vivo desde logs acotados, Python sin buffering y contadores reales Ninja por lote/generación; sin porcentaje global inventado. Barra de actividad, unidades/porcentaje cuando medibles y tiempo transcurrido en Inicio. Pruebas con procesos reales, cancelación/finaltail/timers Tk, revisión independiente y vista real mínima con fixture etiquetada pasan. Implementación integrada; entrega binaria del parche pendiente. |
| UI-SNAP-06 | P2 | HECHA | Codex · PR4 integrado | Portada y fotografías promocionales oficiales solicitadas, tarjetas/CTA/foco inspirados en ReKHCoM; fuentes/pins/copyright explícitos y guard de contenido exacto. Congelado construido, imágenes incluidas, UI observada1020×790/860×730 sin recortes; aprobación independiente. Sin fotos privadas ni datos extraídos; entrega binaria del parche pendiente. |
| FOTO-02 | P0 | HECHA | Claude / revisión Codex | Herramienta de auditoría CPU del PR1 integrada, revisada y probada (25casos), incluidas correcciones para no llamar limpio a material incompleto. Auditoría real RTX de2fotos/2miniaturas pasa. Finaliza la herramienta, no el fallo gráfico AMD: bandas/captura/cierres continúan en FOTO-01 con Claude/Fable. docs/bugs/photo-audit-review.md. |
| RELEASE-06 | P0 | HECHA | Codex · 2026-11-14 | Publicada v0.6.0-alpha, productor82e01064 y cuatro assets inmutables verificados. CI/416tests (1skip), auditoría independiente, instalación/reparación/reconstrucción offline real, launcher final y pruebas RTX acotadas pasan; updater descarga/stage1105archivos publicado, tag/canal exactos sin Latest/avisos stable. No cierra hardware AMD, color/fotos, cabeza ni mandos. docs/bugs/v06-package-acceptance.md. |
| KIT-SCOPE-06 | P0 | HECHA | Codex · 2026-11-14 | Pycache con ruta local y tres headers DLSS sin pin retirados antes de publicar. Productor82e01064: allowlist SDK con doble verificación/recibos canónicos, import del helper en temporal privado y guard final bytecode. Doce tests focalizados y revisión independiente; auditoría final1105/7310hashes sin hallazgos y reconstrucción offline real pasan. Candidatos8f inmutables/no publicados; docs/bugs/v06-package-acceptance.md. |
| DIAG-HISTORY-01 | P2 | HECHA | Codex · 2026-11-14 | Scan completo con heaps4/2, memoria constante y cancelación; reproduce omisión de entrada257, quince tests (una omisión symlink), revisión independiente y exportación GUI congelada entre601archivos pasan. Código launcher final idéntico al probado salvo timestamps/checksum PE; docs/bugs/diagnostic-history.md y docs/bugs/v06-package-acceptance.md. Sin borrar historial ni prometer corrección gráfica AMD. |
| PACE-CRC-01 | P2 | HECHA | Codex · 2026-11-14 | IEEE CRC32 portátil integrado/revisado: siete tests y2176casos de Cpu completo, disassembly de función real y540s de fotos/primera expedición RTX pasan. Dos pares inversos mismoexe/cachés verificadas: p99 agrupado39,903→32,037ms; máximo empeora en un par y fase posterior no mejora uniformemente. No promete másFPS ni cierre AMD; opt-out conservado. docs/bugs/crc-isa.md. |
| RELEASE-051 | P0 | HECHA | Codex · 2026-11-14 | Publicada v0.5.1-alpha sobre e77393f4, prerelease fuera de Latest. Cuatro assets remotos coinciden por hash/tamaño, tag exacto, descarga/stage real y catálogo manual correctos; ningún aviso automático alpha. Paquete/kit/reconstrucción/GUI verificados. docs/bugs/v051-package-acceptance.md; aceptación física AMD y bugs del juego siguen en sus filas. |
| KIT-RECOVERY-01 | P1 | HECHA | Codex · 2026-11-14 | Recuperación local de caché corrupto revisada y entregada en 0.5.1. Candidato verificado, lock/cuarentena/rollback y concurrencia probados, sin red implícita ni tocar imports. Cuarentenas se conservan. docs/bugs/session-identity-and-kit-recovery.md. |
| LOG-IDENTITY-01 | P1 | HECHA | Codex · 2026-11-14 | Entregado en 0.5.1: SHA real de ejecutable, claims separados, exit observado y análisis de sesión redactado. Proceso CPU real del binario final registra SHA correcto, marcador coincidente y exit0; GUI congelada exporta análisis. Triaje CPU del PR2 integrado; applets no. |
| PACE-TRACE-01 | P1 | HECHA | Codex · 2026-11-14 | Instrumentación entregada en 0.5.1, no una mejora de pacing declarada. FIFO/Mailbox RTX reales registran cuatro operaciones y modos/imágenes efectivos; 32 líneas/sesión corta. Checkbox opt-in y offpath sin reloj verificados. FreeSync/AMD y optimización siguen PACE-01/VRR-01. |
| UI-TECH-01 | P1 | HECHA | Codex · 2026-11-14 | Entregado y revisado en launcher congelado 0.5.1: Original/Bajo/Medio/Alto/Ultra, tooltips y nombres técnicos; presentación solicitada/efectiva separadas. Presets conservan timing/color/controles y manual pasa a Personalizado. |
| BRAND-01 | P1 | HECHA | Codex · 2026-11-14 | Entregado en 0.5.1: nombres visibles newsnap, logs/config y hints. Pruebas nativas de rotación y compatibilidad, compilación completa y sesiones RTX preservan INI antiguo. Atribuciones y archivos legados conservados. |
| DIAG-01 | P1 | HECHA | Codex · 2026-11-14 | Exportación GUI real congelada 0.5.1 validada con log sintético: ZIP con resumen/log/análisis JSON. Revisión de privacidad, rutas con espacios, fallos/cancelación y USB/exFAT; sin juego/fotos/partidas/secretos ni subida automática. Aceptación física del propietario separada. |
| LAUNCH-404 | P0 | HECHA | Codex · 2026-11-14 | Corregido y entregado en 0.5.1: kit completo incluido y hash fijado. Instalación/reparación real y extracción del bundle con red prohibida, luego reconstrucción desde su Python portable, correctas. Descarga inicial del repo privado requiere acceso; reconstrucción ya no necesita descargar el kit. |
| AUTO-DATA | P0 | HECHA | Codex · 2026-11-14 | Corrección entregada 0.5.1: detección acotada de imports completos directos/anidados/vecinos, sin preferencias obsoletas que los oculten. Pruebas de layouts/presencia/estado y GUI congelada con marcador sintético correctas. No modifica imports ni sustituye su verificación. |
| HOME-PROFILE | P1 | HECHA | Codex · 2026-11-14 | Entregado 0.5.1: selector fuera de Inicio, en Opciones → Juego; perfil/modelo y bloqueo busy preservados. Jerarquía/callbacks Tk y GUI congelada revisados. |
| CONSOLE-01 | P1 | HECHA | Codex · 2026-11-14 | Entregado 0.5.1: helpers Python/Ninja/probes ocultos y reexec/restart sin consola cuando viene del launcher. Tests nativos/Job/exit/cleanup, compilación real y launcher congelado correctos. Consola CLI explícita preservada; no se cierran CMD ajenos. |
| RELEASE-05 | P0 | HECHA | Codex · 2026-11-13 | `v0.5.0-alpha` publicada sobre `e314751d`, prerelease y fuera de Latest estable. Dos ZIP públicos + dos SHA256 remotos verificados; compilación real desde el kit y 540 s/fotos/tutorial del nuevo binario correctos, actualización/reparación/kit descargados de la release publicada. 0.4 intacta. Evidencia `docs/bugs/v05-alpha-acceptance.md`; AMD/mando/FreeSync mantienen pendientes. |
| FOCO-01 | P0 | HECHA | Confirmación del propietario · RX 6900 XT | El propietario confirma «el cuadrado de foto se ve bien ahora en 6900xt». Cierra ese defecto visual reportado; no cierra fotos guardadas, color, crash ni todas las variantes de zoom/HUD. No atribuir una causa concreta sin traza. |
| UI-01 | P0 | HECHA | Codex · 2026-11-14 | Bloque de launcher entregado en 0.5.1 y verificado por sus consumidores finales: kit offline/404, autodetección, perfil en Opciones, helpers, presets/tooltips y diagnóstico. La confirmación externa RX6900XT permanece QA-AMD-01; no cerrar bugs de fotos/color/cabeza. |
| ART-01 | P1 | HECHA | Codex · 2026-11-13 | Localizar el mando pixelado ORIGINAL de ReKHCoM y adaptarlo a Switch (A derecha/B abajo/X arriba/Y izquierda, L/R/ZL/ZR/+/-/sticks). Referencia canónica indicada abajo. Salida `assets/controllers/` + procedencia; no copiar sprites del juego. Original 104×72 conservado por SHA, overlays nativos Switch y escala entera 4×; revisión visual `build/launcher-audit-v05/controller-switch-after.jpg`, pruebas de selección/desconexión. Sin activar sensores físicos. |
| CACHE-01 | P2 | HECHA | Codex / agente de mantenimiento | Caché privada de C generado, con import/recipe/dependencias verificadas, límite y limpieza segura. Reservados `generation_cache.py`, `build.py`, `maintenance.py`, tests y `docs/GENERATION_CACHE.md`. Revisión independiente aprobada tras corregir identidad LZ4 y módulos inesperados; ensayo real `build/v05-generation-cache-real/evidence.json`: generación 86,820 s frente a restore 3,044 s + verificación 0,265 s, 150 archivos idénticos, sin reutilizar ejecutables. |
| QA-01 | P1 | HECHA | Codex · 2026-11-13 | Aceptación de la alpha publicada revisada independientemente: catálogo alpha manual, ningún aviso de stable inexistente, descarga y stage real, instalación/reparación de misma versión, 1103 hashes, tres sentinelas conservados, launcher con PATH limpio y kit exacto descargado/reutilizado offline. Compilación real del GameData 0.4 copiado comprobada por separado. Rechazos/cancelación cubiertos por suite de 299; ver `docs/bugs/v05-alpha-acceptance.md`. |
| KIT-ALPHA-01 | P0 | HECHA | Codex / revisor de mantenimiento · 2026-11-13 | Adquisición del kit alpha/dev exacto de la versión instalada corregida y revisada; regresión rojo→verde, 30 pruebas específicas y suite completa de 299. Mantiene tag/revisión/assets/hashes/inventario y rechazo de drafts/versiones ajenas. Los avisos automáticos siguen solo stable. Archivos `newsnap/build_kit.py`, `tests/test_build_kit.py`. |
| LEARN-01 | P2 | HECHA | Codex · 2026-11-13 | Consolidar lecciones verificadas para OptiPort y matriz AMD/NVIDIA. Crear `docs/bugs/GPU_MATRIX.md`; separar observado/inferido/corregido/validado por GPU. Revisado y promovido a OptiPort `9673006`; siete referencias instaladas en Codex, checkout activo y cambios locales de Claude preservados. Evidencia/matriz en `docs/bugs/GPU_MATRIX.md`. |


## Archived Spanish board (before the English rewrite, 2026-11-14)

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

Las tareas terminadas se conservan en [historial de trabajo completado](PENDIENTES-HECHOS.md).
Última entrega: [0.8.1-tester](https://github.com/MatyMeatBoy/NewSnapRecomp/releases/tag/v0.8.1-tester)
(notas en `docs/releases/0.8.1-tester.md`).

## Estado al día (2026-11-14, tras 0.8.1-tester): leer primero

Para cualquier modelo que retome el trabajo:

- `main` contiene 0.8.1-tester: lo de 0.8.0 más SS-02 (resolución interna por escalado en el host,
  sombras), FPS-01 (90/120/144, Codex) y FG-01 (generación de fotogramas FSR, apagada por defecto).
- **En curso, Claude: SS-02** (escala interna 125/150/200 %). Rama `claude/ss-02-*`. Reservados
  los adaptadores de supersampling (`snap_supersample`), `docs/SUPERSAMPLING.md` y la opción de
  escala en `launcher.py`.
- **En revisión, Codex / PR #20: FPS-01** (modos opcionales 90/120/144 FPS, `docs/HIGH_FPS.md`). No tocar los
  archivos de SS-02 sin coordinar aquí.
- **Cola de Claude después de SS-02** (pedido del propietario, 2026-11-14): pasar todo el repo a
  inglés (docs, textos de commit/PR futuros; la interfaz del launcher mantiene sus idiomas) y
  añadir imágenes del juego corriendo al README.
- También pedido (2026-11-14), después de SS-02: limpiar `tools/pruebas-amd` (hecho en la rama de
  SS-02); sombras de vegetación de más resolución (las de personajes ya se ven finas, las de plantas
  siguen al tamaño del juego); ultrawide si es posible (el donor trae `resolution.c` wide con sitios
  de Astral: hay que encontrar los de Snap y mantener las fotos en 16:9); frame pacing y cargas en
  los modos extendidos; launcher con la mayor compatibilidad de volcados (NSP, NSZ, XCI, XCZ y
  carpetas `exefs`/`romfs` ya extraídas).
- Regla del propietario: antes de cada solución, buscar cómo lo resolvieron otros recomps y
  emuladores (Astral, TotK, Witch Time, LAS, Lichii, Savage Wind, yuzu/Ryujinx) y citarlo.
- Receta de release en esta máquina: sección «Receta de release» al final de este archivo.
La cola siguiente conserva únicamente investigación o aceptación pendientes.

## Tareas y reservas

**Coordinación inmediata: FOCO-01 está HECHA por confirmación del propietario
en RX 6900 XT; no duplicar ese fix.** Claude lleva FOTO-01 (bandas, cierres y
diagnóstico GPU); su PR6 ya está integrado con correcciones de revisión. FOTO-02, la herramienta de auditoría,
ya está en el historial. Codex integró PR4/5/6/7/8/9/10 y conserva pendiente el turno GPU
para su aceptación interactiva final. El propietario confirma que el primer nivel
0.6 ya no se ve oscuro y parece funcionar a60FPS; esa confirmación no cierra las
fotos ni constituye una validación completa AMD/VRR/mando. Reporte histórico:
`docs/bugs/RX6900XT-REPORTES.md`.

| ID | Prioridad | Estado | Responsable | Trabajo y archivos reservados |
|---|---|---|---|---|
| CPU-WORKER-07 | P2 | REVISIÓN | Codex / CPU · 2026-11-14 | Analizar operación de recursos main+5ec890 y latencias de virtual core ya medidas. Buscar coste de lifting reducible manteniendo Cpu/memoria/yields; sin cambiar prioridades/simulación ni pruebas GPU concurrentes. Prototipo privado probado con Cpu completo/trazas/alias/streams y controles negativos; especialización UINT32_MAX aumenta código O1/O2 sin ganancia medida. No se integra como optimización. Reserva liberada; queda medida comparable si surge un candidato útil. |
| LAUNCH-POSTBUILD-06 | P0 | REVISIÓN | Codex · PR4/5 integrados | Dos causas corregidas: marcador de shaders sin registros bloqueaba el primer inicio; --boot ejecutaba una sonda que salía0 en primera NVN. PR4/5 integrados, CI y regresiones rojo→verde/revisión independiente. Prueba congelada anterior reprodujo exactamente el cierre0; queda observar ventana/frames en modo interactivo con el congelado corregido, cuando el turno GPU de Claude termine. No modificar GameData original ni la release0.6 publicada. |
| POOL-BOUNDS-01 | P1 | REVISIÓN | Codex / investigación · 2026-11-14 | Condición de solapamiento reproducida en CPU. Logging limitado a 16 color + 4 DS y experimento AC_SNAP_POOL_BOUNDS=1 integrado, apagado por defecto. Cinco pruebas nativas/sintaxis/concurrencia pasan; no es fix AMD ni prueba de causa. Ver docs/bugs/pool-allocation-bounds.md. |
| HEAD-INTRO | P1 | REVISIÓN | Claude / Codex · PR #3 | PR y correcciones de revisión integrados: medida RTX de una toma, sin causa identificada ni fix. Intervención de timer concreta no cambia esa trayectoria; no descarta universalmente GPU/pacing/CRC. Tool conserva segmentos/paridad al descartar pares; diez tests y cuatro mediciones guardadas verificadas. Pendiente referencia comparable y JSON auditable de 30 FPS. docs/bugs/head-intro-stutter.md. |
| KEYBOARD-CRASH | P0 | REVISIÓN | Claude / integración Codex · PR #2 | PR integrado con bool exacto false, cuatro overrides de cuenta no fundamentados retirados y lectura de variante12bytes. Cuatro tests nativos/headerreal pasan. Se conserva triage nuevo de main y se acotan inferencias docs. Recorrido RTX540s por fotos/evaluación/primera expedición y60s del binario final pasan; causa del teclado/cierre AMD no acreditada. docs/bugs/pr2-applet-contracts.md. |

| RELEASE-07-TESTER | P0 | REVISIÓN | Claude · 2026-11-14 · orden directa del propietario | **Publicada como prerelease [v0.7.0-tester](https://github.com/MatyMeatBoy/NewSnapRecomp/releases/tag/v0.7.0-tester)**, productor `7e1b1c39`. Kit y ZIP cerrados por sus scripts; runtime reconstruido desde el kit con su Python incluido (selftest y cargador correctos); ruta de fotos en RTX 4060 con ese runtime: cuatro copias sin diferencias, sin fatal, terminada por cierre de ventana en el fotograma 23359. **No repetidas** la instalación aislada con el actualizador ni la prueba del launcher congelado de 0.6. Nada ejecutado en AMD. No corrige los fallos AMD ni sustituye a 0.6. Evidencia local `build/v07-tester-*`. |
| FOTO-01 | P0 | REVISIÓN | Claude / revisión Codex · PR #6 · 2026-11-14 | **Tercera ronda: causa encontrada y corregida en AMD.** El volcado F12 de la prueba 6 mostró que la miniatura es una BC1 2D que el juego codifica dibujando por vistas de bloques; el controlador RDNA 1/2 escribe fuera de esas imágenes (issue #5 del donor, ya evitado allí solo para BC 3D). `newsnap/bc_block_views_adapt.py`: `AC_BLOCK_VIEWS`, por defecto 0 en `vk_caps.amd_sc` (NVIDIA sin cambio), BC 2D por imagen intermedia refrescada por pase. Probado en la RX 6900 XT: miniatura completa, interfaz limpia, sin `write invalid` (una sesión). Pendiente: más niveles/álbum/cuadrados y control RTX con `AC_BLOCK_VIEWS=0`. Ver `docs/bugs/amd-photo-gpu-fault.md`. Reservados además `bc_block_views_adapt.py`, `test_bc_block_views.py`. — Historial: Dos logs 0.6 RX 6900 XT reportan write-invalid y fotos con bandas; causa no acreditada. Diagnóstico GPU→buffer siempre activo, PNG opt-in, asignación best-effort y presupuesto atómico de 64 MiB pendiente. Shadow permanece experimento AC_SHADOW=1 explícito, sin default por vendor ni aceptación AMD. Tests nativos: fallos de ambas asignaciones, cleanup parcial, límite de 24 sin PNG y presupuesto pendiente; PR6 integrado; runtime privado compila y pasa selftest/loader; entrega pública y prueba física pendientes. Nuevo log confirma shadow activo y el mismo tipo de fault, sin demostrar causa FSR4 ni estado de fotos. Ver docs/bugs/integration-07.md. No inferir visibilidad CPU/JPEG ni causa import/driver desde mismatch GPU. Reservados photo_readback_adapt.py, test_photo_readback.py, amd-photo-gpu-fault.md; evidencia privada build/foto01-*. **Segunda ronda del propietario (0.6, RX 6900 XT):** la miniatura de la foto ya sale con franjas dentro del nivel (patrón fijo, 1 de cada 4 tramos), también retrato del profesor, placa del nombre y marco; vuelven los cuadrados de GPU-WRITE-01; con `fifo` el retrato sale bien; shadow no cambia el aspecto. En RTX todo limpio; dentro del nivel la foto es un pase de dibujo sin copias. PR #11 (Claude): línea `amd_diag:` con los ajustes A/B en cada log y seis `.bat` de descarte en `tools/pruebas-amd/`; la combinación conservadora pasa la ruta de fotos en RTX. Pendiente del propietario: pruebas 1 a 6 en la RX 6900 XT. |
| TUTO-01 | P0 | EN CURSO | Codex / coordinación con Claude | El propietario pudo elegir carpetas de Pikachu/Vivillon y avanzar; después reportó teclado de Windows y cierre tras registro/evaluación de Pikachu. Ver KEYBOARD-CRASH. No cambiar lógica de sujetos/progreso ni recuperar el perfil anterior: recuperación excluida por el propietario. |
| INPUT-01 | P0 | REVISIÓN | Codex · 2026-11-13 | Cámara apunta sola: auditar mouse relativo, foco inicial, sticks y gyro; comprobar reposo, reconexión y cambio mando/ratón. Integrados `newsnap/camera_input_adapt.py` + `tests/test_camera_input.py`; 19 escenarios nativos y revisión independiente. Aceptación con mando/mouse físico pendiente. Sin activar sensores/vibración físicos por sorpresa. |
| GPU-WRITE-01 | P0 | REVISIÓN | Codex / agente de render | Draws gráficos con escrituras SSBO/imagen no pueden omitirse durante compilación. Fix específico integrado, 11 casos nativos y revisión independiente aprobados; compute ya era síncrono y queda descartado. `graphics_effects_adapt.py`, `tests/test_graphics_effects.py`, `docs/bugs/graphics-side-effects.md`. Binario integrado en prueba; causalidad AMD pendiente. |
| COLOR-01 | P0 | REVISIÓN | Codex / renderer | Actualización0.6: propietario confirma que el primer nivel ya no se ve oscuro en RX6900XT y parece funcionar bien a60FPS. Confirmación acotada a esa escena; no es benchmark ni cierra fotos, otros modos o saturación de todas las escenas. Reporte anterior: saturación excesiva con ZIP0.5. Las nuevas capturas muestran HUD «AMD FSR 1, sharpness 80%»; comprobar runtime realmente iniciado al forzar lanzamiento, configuración efectiva y formato/transferencia. No bajar saturación arbitrariamente ni declarar equivalencia AMD por la prueba RTX. |
| PACE-01 | P1 | EN CURSO | Codex / agente de render | Puente entero con equivalencia completa y guardas de original/receta integrado; A/B local de dos pares inversos reduce p99 42,970→25,469 ms, conserva mediana ≈16,67 ms y aún registra pico 107,692 ms. Evidencia `build/v05-rng-pacing-ab/`; archivos `random_range_adapt.py`, `snap_random_range.*`, `test_random_range.py`, `cpu-asset-workers.md`. Aceptación final alpha RTX completada; AMD pendiente y virtual-core starvation sigue documentada, sin alterar prioridades/simulación. |
| PACE-AMD-01 | P1 | LIBRE | — · 2026-11-14 | RX 6900 XT, 0.7.1-tester: el propietario nota irregularidad al girar la cámara rápido. Compatible con judder de cadencia: el controlador AMD de Windows no ofrece `mailbox` y cae a `fifo`, y 60 fps en un monitor de 100 Hz alternan 10/20 ms. Logs: 60,0 fps de media, 1 % low 49–58, picos aislados ≤54 ms en espera de fence/present. Sin medir. Siguiente: repetir con el monitor a 120 Hz o FreeSync activo y con traza de presentación; separar cadencia del monitor de picos del runtime. No cambiar el modo de presentación sin esa medida. Ver `docs/releases/0.7.1-tester.md`. |
| CRISTAL-01 | P1 | REVISIÓN | Claude · 2026-11-14 | **Corregido en AMD:** `newsnap/spirv_nminmax_adapt.py` reescribe cada módulo al crearlo: FMin/FMax/FClamp→NMin/NMax/NClamp (semántica de Maxwell) y Sqrt/InverseSqrt/Log2 con NMax(x,0). `AC_SPIRV_NMINMAX` y `AC_SPIRV_DOMAIN_CLAMP` activos en AMD, apagados en el resto. Prueba 10 en la RX 6900 XT: cristal correcto y 0 pases con NaN (volcado f8681); spirv-val OK en 89 shaders. Pendiente: A/B para atribuir cuál de los dos ajustes lo arregla, y control en RTX. Guía para otros recomps: `docs/bugs/amd-nan-shader-math.md`. — Historial: RX 6900 XT, 0.7.1-tester: el centro de cristal de la Cristalflor sale negro. Volcado F12 f47390: el pase de escena (52 dibujos) no tiene NaN; el pase siguiente, un solo dibujo transparente (vs cc2c6ed76addc42d / fs 4dbd63498689dbcc; BC5 normales, BC1 color, 2 mapas de sombra, cubemap BC6H; mezcla src 5 dst 16), deja 55.836 píxeles NaN que se ven negros. Hipótesis: semántica de coma flotante del shader traducido (p. ej. 0×∞ o rsqrt(0) que en la Switch dan 0) distinta en el controlador AMD. Sin comparación RTX del mismo plano. |
| GYRO-01 | P0 | REVISIÓN | Claude · 2026-11-14 | Activar el giroscopio en las opciones cerraba el juego: `FATAL: ipc: hid command 82 is not implemented` (IsSixAxisSensorAtRest, llamado por el cliente hid del SDK; log de la prueba 8 en RX 6900 XT, independiente de la GPU). `newsnap/hid_six_axis_adapt.py` contesta los comandos de seis ejes 68–83 del IHidServer (ajustes aceptados, consultas con valores por defecto del SDK, reposo según el movimiento real). `tests/test_hid_six_axis.py`. Falta prueba física con el giroscopio activo. |
| PAD-01 | P1 | REVISIÓN | Codex / agente de controles | Backend SDL de prueba de mandos implementado y probado con dispositivos virtuales/ABI real. Reservados `controller_probe.py`, `controller_ui.py`, `tests/test_controller_probe.py`. UI visual se integra con ART-01. |
| VRR-01 | P1 | REVISIÓN | Codex / agente de render | Estado real de presentación por VK_EXT_present_timing, unknown/fixed/variable; nunca inferir VRR por FIFO/mailbox. Reservados `vrr_adapt.py`, overlays `snap_vrr*`, `display_status.py`, `display_ui.py`, tests y `docs/DISPLAY.md`. Prueba swapchain real integrada completada: API disponible, intervalo cero → unknown, sin inferir VRR. Validación FreeSync física pendiente. |
| MENU-01 | P1 | REVISIÓN | Codex / agente de render | Menú dentro del juego: Original/Auto/DLSS/FSR 3.1/FSR 4, Native AA/DLAA y tres presets reducidos. Quitar FSR 3 genérico, XeSS/FSR espacial y opciones artísticas ignoradas. Reservados `menu_adapt.py`, `tests/test_snap_menu.py`. |
| SS-02 | P1 | REVISIÓN | Claude · 0.8.1-tester | Resolución interna por escalado en el host, 125–300 % y «Según la pantalla», cadena 16:9, `shadow_scale` para los mapas de sol de Snap. RX 6900 XT: 200 % a 60 y 120 fps, fotos correctas. Falta RTX y puntuación comparada. `docs/SUPERSAMPLING.md`. |
| FG-01 | P2 | REVISIÓN | Claude · 0.8.1-tester | Generación de fotogramas FSR (SDK 2.4, sin swapchain de FFX), `frame_gen = fsr`, apagada por defecto, solo con FSR 3.1/4. `newsnap/framegen_adapt.py`, `overlays/snap_fsr_fg.c`. RX 6900 XT: frames reales a 16,667 ms con `immediate`. Falta: imagen sin HUD, DLSS-G, ritmo con VRR y monitores de 100 Hz. |
| FPS-01 | P1 | REVISIÓN | Codex · PR #20 · 2026-11-14 | Opciones integradas 30/60/90/120/144, 60 por defecto, sin uncapped; metadata exige runtime nuevo. Reservas de implementación liberadas: high_fps_adapt.py, overlays snap_high_fps.*, patches snap-2.0.1-high-fps.txt, selector FPS exclusivamente en launcher/settings, capacidad en version.py sin cambiar release, adapt/build y tests de la receta. Sondas de solo lectura timer/rail/UI y check_fps_rail.py. Cinco pasadas RTX 180 s con mismo binario/perfil/ruta/caché salen 0 y conservan origen; tramo rail 10 a 80 tarda 87,969–87,971 s a todos los caps, dentro de variación de dos controles 60. CI 493 tests pasa (34 omitidos Linux); Windows 483 pasa (16 omitidos) y fila FPS nativa adicional. No acredita todo HUD/menú, foto/puntuación/persistencia ni AMD/FreeSync; un warm boot aislado falló SwitchToFiber(0) antes de presentar, causa sin atribuir. Cuatro controles de arranque posteriores pasan. Pedida revisión; no marcar HECHA. Integrado main/PR #21 en la rama del PR: 485 tests Windows pasan (16 omitidos), CI 494 pasa (34 omitidos Linux). RTX: 90 s a 144 nativo y dos pasadas 120 + Internal x2 salen 0, targets 3840x2160, HUD/miniaturas completos, sin fallos de shader/draws omitidos; caché x2 caliente elimina la espera de traducción observada, quedan picos. No es aceptación AMD ni toda foto/evaluación. Evidencia privada build/fps01/, informe docs/HIGH_FPS.md. Conserva la implementación de SS-02 de Claude. |
| GYRO-02 | P1 | REVISIÓN | Claude · 0.8.0-tester | Pestaña Mods, `gyro_sens` 2,5 por defecto (0,1–10, en vivo). Falta prueba con mando físico. |
| PIPE-MO-01 | P2 | REVISIÓN | Claude · 0.8.0-tester | Prewarm de los pipelines del pase de movimiento por objeto (99 de 286 registros se descartaban). |
| PRESENT-WIN-01 | P1 | REVISIÓN | Claude · 0.8.0-tester | Ventana compuesta sin `mailbox` → `immediate` (`AC_WINDOWED_IMMEDIATE=0` lo desactiva). Medido en RX 6900 XT. |
| QA-AMD-01 | P0 | EN CURSO | Codex / propietario · RX 6900 XT | Prueba física0.6 en curso: propietario confirma primer nivel sin oscuridad y funcionamiento aparente a60FPS. Fotos/miniaturas siguen corruptas y dos cierres actuales registran escritura GPU inválida. Claude trabaja en esos fallos. Evidencia histórica ZIP0.5: Recuadro de foto confirmado correcto; fotos/miniaturas y color fallan; cabeza vibra en intro; launcher falla y cierre tras teclado Windows. Registrar launcher/version/hash del runtime por separado, ya que hubo lanzamiento forzado. No declarar toda AMD validada. |

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
  `codex-clipboard-473be5db-…`, `codex-clipboard-b8af3c5e-…` en su carpeta temporal local.
  Copiar a `build/user-reports/` para inspección, sin añadirlas a Git.

## Referencia de ReKHCoM para ART-01

El `LEEME.md` de la carpeta local `ReKHCoM-build` señala como mapa canónico el
`LEEME.md` y el `CLAUDE.md` del proyecto local `KHCoMPC` del propietario.
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

## Futuras (pedidas por el propietario, después de 0.7.1; estado a 0.8.0)

Orden sugerido. Ninguna cambia la lógica del juego; cada una necesita medida antes de darla
por buena.

1. **HECHO en 0.8.0-tester (GYRO-02).** Pestaña «Mods» en el launcher.
   - Llevar a ella el giroscopio (`motion`, ya existe y está activo por defecto) y la
     sensibilidad del ratón.
   - Añadir `gyro_sens`: por defecto 2,5, rango 0,1–10, ajustable en vivo. El propietario siente
     la base actual como un «2» de shooter y la quiere en «5». Plan: escalar el giroscopio antes
     de integrarlo en `motion_fusion.c` y, si la escala no es 1, sin la corrección por gravedad.
   - Texto de ayuda sobre mandos compatibles sin drivers: Pro, Joy-Con, DS4, DualSense y 8BitDo
     en modo Switch (en modo X-input no envían giroscopio).
   - Proponer un layout de teclado para este modo.
2. **(FPS-01, otro modelo)** **FPS altos con presets 30/60/90/120/144/240 y libre**, solo si la lógica del juego no
   cambia. Base: `docs/HIGH_FPS.md` (temporizador con canales fijos a 1/60 por medir).
   - Antes, medir la sensación de que algunas animaciones van a 30 fps. Puede ser judder de
     60 fps en 100 Hz con `fifo` (PACE-AMD-01) o animaciones a mitad de ritmo propias del juego.
3. **Pacing en AMD (PACE-AMD-01):**
   - Tirones al girar la cámara rápido.
   - Pruebas: monitor a 120 Hz o FreeSync, y traza de presentación.
   - Ajustes del sistema a probar (no son del código): reloj mínimo en Adrenalin, MPO.
4. **Renderizado interno y sombras (SS-02, Claude en curso).**
   - Escala ×2 «como otros juegos»: hoy existe 125/150/200 % experimental solo en TV
     (`docs/SUPERSAMPLING.md`); falta validar fotos y puntuación a esa escala.
   - Sombras de más resolución o calidad: existe `AC_SHADOW_RES`/`AC_SHADOW_SCALE`, sin medir en
     Snap.
5. **Fotos a mayor resolución** que 1080×720 en el álbum (mod opcional). Requiere ver cómo
   guarda y puntúa el juego.
6. **CRISTAL-01:** A/B de `AC_SPIRV_NMINMAX` y `AC_SPIRV_DOMAIN_CLAMP` para atribuir la causa, y
   control en RTX.

## Hoja de ruta AMD (RDNA 2 y siguientes)

Estado tras 0.7.1-tester: fotos, interfaz, cierres, giroscopio y Cristalflor corregidos y
probados en la RX 6900 XT. Lo que sigue va ordenado por impacto. La columna NVIDIA indica si el
cambio también le sirve: es aceptable siempre que no empeore lo que ya funciona allí.

| # | Tema | Qué hacer | ¿Sirve en NVIDIA? |
|---|---|---|---|
| 1 | Pacing (PACE-AMD-01) | Medir con traza de presentación los tirones al girar la cámara. Probar 120 Hz o FreeSync; valorar `fifo_relaxed` cuando no hay `mailbox` | Sí, la medida y los presets de FPS |
| 2 | FPS altos con presets 30–240 | `docs/HIGH_FPS.md`: medir los canales del temporizador fijos a 1/60 antes de tocar nada; sin cambiar la lógica | Sí |
| 3 | Atribución de CRISTAL-01 | A/B de `AC_SPIRV_NMINMAX` y `AC_SPIRV_DOMAIN_CLAMP`. Si el control en RTX da imagen idéntica, valorar activarlo en todas las GPU: es la semántica de la Switch | Posible, tras el control RTX |
| 4 | Otros NaN y negros | Revisar cada volcado buscando pases con `nan` mayor que 0 (`docs/bugs/amd-nan-shader-math.md`); recorrer más niveles y el álbum | Sí, el método |
| 5 | Vida útil de memoria | Liberación diferida hasta que termine el envío (TotK, `amd-native-source-audit.md`). Es la clase de fallo de los `write invalid`, todavía sin portar | Sí, es una corrección general |
| 6 | Compilación de pipelines en RDNA 1/2 | GPL apagado: medir esperas y omisiones de dibujo en recorridos largos y mejorar la preparación de shaders para que no haya tirones la primera vez | Parcial |
| 7 | FSR 4 en RDNA 2 | Comparar coste y calidad con FSR 3.1 en la 6900 XT y elegir el valor por defecto según la arquitectura | No (FSR 4 depende del controlador de AMD) |
| 8 | Robustez del traductor | Bloque de retorno tras CAL incondicional y enumeración Vulkan con `VK_INCOMPLETE` (`amd-emulation-source-audit.md`) | Sí |
| 9 | Renderizado interno y sombras | Escala ×2 validada con fotos y puntuación; sombras de más resolución medidas en Snap | Sí |
| 10 | Limpieza | Retirar de la documentación el experimento `shadow = 1` (no era la causa de nada) y las pruebas `.bat` ya superadas | — |

Reglas que siguen vigentes: una prueba en AMD no valida NVIDIA ni al revés. Todo cambio por
fabricante debe tener un ajuste para desactivarlo, y nada se marca HECHO sin una prueba física.

## Receta de release (PC del propietario)

Clon en `D:\01Claude\NewSnapRecomp\repo` (`core.autocrlf=false`, `core.eol=lf`), `.venv` con
Python 3.12 y `requirements-release`. SDK en `D:\01Claude\NewSnapRecomp\sdkroot` (kit 0.7.0).
Pasos: merge del PR → `python -m tools.package_build_kit --sdk-root <sdkroot>` →
`tools/build_launcher.py` → `python -m tools.package_windows_release` → verificar kit y
recompilación con PATH mínimo → `gh release create` → instalar con
`updater.stage_update/apply_update` y `maintenance.rebuild_runtime`.
