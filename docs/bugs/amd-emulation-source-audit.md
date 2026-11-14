# AMD / Vulkan — investigación acotada de emulación Switch

Fecha: 2026-11-14. Solo lectura; sin GPU, ROM, claves, perfiles ni cambios de producción. Fuentes primarias enlazadas por mecanismo; las consultas GET y comprobaciones de parentesco se conservan localmente en `build/`. Las prestaciones declaradas por autores no son mediciones nuestras. RX 6900 XT sigue pendiente.

## Resultado útil

1. **Prioridad CPU: CFG del traductor Ryujinx vendorizado.** Una llamada CAL incondicional puede perder su bloque de retorno. El patrón permanece en nuestro árbol; requiere fixture del decoder real antes de modificarlo. Es independiente del trabajo reservado de captura/fault logs.
2. **Robustez de enumeración Vulkan:** nuestro runtime ignora VkResult en las dos llamadas y no reintenta VK_INCOMPLETE. Es un riesgo concreto de inicialización reproducible con stubs, distinto del TOCTOU de Eden. No explica por sí solo una corrupción que aparece ya jugando.
3. Los fixes experimentales de matrices, DCC y query-wait no justifican activar una política AMD global: varios no aplican a RDNA2/Windows o a la arquitectura nativa de Snap. No hay mejora universal demostrada.

## Alcance y familias: no contar forks como motores independientes

- [Eden mirror oficial](https://github.com/eden-emulator/mirror): linaje Yuzu, Switch 1. El mirror conserva commits y Reviewed-on de su forge; comprobé ascendencia de los cuatro commits usados respecto a master.
- [Lichii nx2](https://github.com/zortos293/Lichii/tree/nx2), [Eglantine Community nx2](https://github.com/Eglantine-Community/Eglantine/tree/nx2): código que se presenta explícitamente como **muy experimental Switch 2**, derivado del linaje Eden/Yuzu; no validación equivalente al hardware ni prueba de todos los juegos.
- [Aubepine](https://github.com/pattex67/Aubepine/releases/tag/aubepine-2026-11-10): fork experimental de Lichii nx2 bcb37c49f7, release 837d899184, probado por su autor en RX9070XT/driver propietario y sesiones breves. Incluye Lichii PR573 aunque ésta esté cerrada sin merge upstream. No confundir con **Eglantine PR573**, que trata movimiento ProCon y no AMD.
- [Ryubing](https://github.com/Ryubing/Issues) / Ryujinx: linaje distinto y relevante porque usamos su traductor. El forge git.ryujinx.app no fue accesible desde esta sesión; no adjudico merges a un mirror de tercero. Sus issues de stutter y fallos siguen siendo reportes, no fixes probados. La documentación recomienda Vulkan para AMD, pero eso no demuestra solucionar Snap.
- Citron/Neo: Switch 1. Se localizaron referencias a clasificación RDNA2, pero las URLs de PR no fueron recuperables; no cuentan como fixes confirmados. Vita no es Switch y queda fuera. No se descargaron emuladores.

## Ocho correcciones con estado verificable

### 1. Eden: misma instantánea de extensiones para decidir y validar

[Commit ef4113aeaade8a7055fbedb386837554aead254f](https://github.com/eden-emulator/mirror/commit/ef4113aeaade8a7055fbedb386837554aead254f), 2026-06-15; integrado en master, Reviewed-on PR4072. [Reporte414](https://github.com/eden-emulator/Issue-Reports/issues/414): AMD Vega iGPU/Windows; dos enumeraciones independientes podían discrepar al seleccionar extensiones opcionales. La implementación comparte una sola instantánea. No confundir con mirror PR7 cerrado **sin merge**: el fix integrado tiene otro commit.

**Snap:** `build/source/runtime/vk_device.c:52–60,123–132,248–252` y `vk_caps.c:93–96` realizan count/fill sin comprobar resultados. No existe el mismo circuito Eden decide/valida contra dos listas. Candidato separado: helper acotado que maneje ERROR/VK_INCOMPLETE y memoria; fixture con cambios de count y fallo de fill, sin GPU. Aceptación: no sobrelectura, no extensión habilitada desde datos parciales, fallo explícito si agotados los reintentos. No beneficio FPS esperado.

### 2. Eden: reparación de sincronización y ciclo de consultas tras regresión

[Commit 3d19743d95f973ec0c322a0e8703387513ee0c66](https://github.com/eden-emulator/mirror/commit/3d19743d95f973ec0c322a0e8703387513ee0c66), 2026-06-02; integrado, PR3953. El cambio repara máscaras de etapas y deja de resetear consultas prematuramente. El mensaje atribuye recuperación de FFTactics/Windows AMD y pausa negra de Luigi's Mansion3; incluye también correcciones de otras plataformas, por tanto no hay cifra atribuible a un único ajuste. No publica modelo AMD/driver ni ensayo controlado.

**Snap:** `vk_exec_xfer.c` administra otro ring de occlusion queries, resuelto y reseteado por completion tras fence; `vk_sync.c:149` obtiene timestamps sin WAIT_BIT. El adaptado `vk_exec_xfer.c:216–217` también usa disponibilidad sin WAIT_BIT para oclusión tras fence; no es una mejora nueva a importar. No copiar máscaras parciales de Eden ni cambiar reset a ciegas. El cambio externo refuerza la necesidad de vincular el reset a la última lectura, no prueba un bug local. El código de capturas pertenece a MatyMeatBoy y no se tocó.

### 3. Eden: anotaciones NonUniform repetidas en shaders

[Commit 5ea24621cf8e75fe20ff35c4e41a05baf9497be8](https://github.com/eden-emulator/mirror/commit/5ea24621cf8e75fe20ff35c4e41a05baf9497be8), 2026-05-29; integrado, PR3997. Deduplica IDs decorados en accesos de textura dinámicos y mueve capacidades al setup; el autor lo vincula a LM3/Tomodachi AMD, sin modelo ni prueba física detallada. El commit también cambia una barrera de uploads: no atribuir toda mejora a deduplicación.

**Snap:** usamos backend SPIR-V Ryujinx, no el de Yuzu. `Instructions.cs:590–604` declara capacidades una vez pero aplica NonUniform a objetos; esto no demuestra duplicados del mismo ID, pues los objetos pueden ser distintos. Candidato CPU secundario: shader sintético con índice compartido, guardar SPIR-V, contar decoración por ID y ejecutar spirv-val. No borrar decoraciones necesarias por analogía.

### 4. Lichii: gating de cooperative matrix en AMD RDNA2

[PR657](https://github.com/zortos293/Lichii/pull/657), merged 2026-11-07, **89440b29a90708c0fefc126b2bd8c7a64a996bdd**. Evita HMMA en AMD propietario que anuncia cooperative_matrix sin hardware adecuado, usando la propiedad de mixed-signedness packed integer-dot como proxy RDNA3+. Responde a crash de prebuild en amdvlk64.dll después de d549411. **El autor dice que no lo ha probado físicamente en AMD y solicita tester RDNA2.** No confundir extensión anunciada con modelo/forma útil o rapidez.

**Snap:** `newsnap/upscaler_adapt.py:17–44` habilita extensiones SDK consultadas; no baja instrucciones HMMA del juego a cooperative matrix. `snap_fsr_sdk.c` deja selección/create al proveedor oficial. No trasplantar proxy RDNA3 ni alterar modo Original. Útil para verificar que errores del proveedor dejan un fallback explícito, no para declarar solucionado FSR4 en 6900XT.

### 5. Lichii: coherencia workgroup al usar Vulkan memory model

[PR1698](https://github.com/zortos293/Lichii/pull/1698), merged 2026-11-14, **ca063c0a801cb27471fce9d16240b32959499af2**. La ruta cooperativa emitía accesos shared/barriers con semántica GLSL450 pese a seleccionar Vulkan memory model. Añade operandos de visibilidad/disponibilidad y NonPrivatePointer. Evidencia CPU: tests, comparación de módulos, spirv-val y compilación RADV offline gfx1100/gfx1201; no ensayo físico de juego con la corrección. Alcance declarado NVIDIA RTX y AMD RDNA3/4 que toman ese lowering.

**Snap:** el traductor vendorizado no contiene esa nueva ruta HMMA cooperativa. La presencia de soporte cooperative_matrix para SDK no introduce por sí misma el mismo IR. No aplicable como patch directo; comprobar memoria-modelo de shaders reales antes de proponer barreras adicionales.

### 6. Lichii: preservar clasificación de punteros SSBO al re-traducir pipeline evictado

[PR1143](https://github.com/zortos293/Lichii/pull/1143), merged 2026-11-09, **d2eaae4f3abca636b030b726f107bace06f61079**. El pipeline recreado con slot temporalmente nulo/perdido pasaba a leer ceros para el resto de sesión. Conserva las claves de slots conocidos, mapa acotado8192 y diagnóstico limitado. Tests CPU/syntax; evidencia física del caso largo pendiente. El autor excluye un caso distinto de registro de disco ya guardado con slot nulo.

**Snap:** `newsnap/adapt.py:121–143` ya introduce copia de control metadata propiedad del programa para la ejecución diferida. Eso previene vida útil de metadata, no equivale al fix de clasificación. No se encontró la maquinaria EvictedPointerSlots de Lichii; candidato de test conceptual: reusar exactamente shader/metadata después de destruir programa original y variar binding. No declarar el defecto Lichii presente aquí.

### 7. Lichii: realizar clear diferido antes de copy/blit ajeno al renderpass

[PR185](https://github.com/zortos293/Lichii/pull/185), merged 2026-11-06, **f99fb8ab7b604f60d3b25cae3a8c39f1ae258c09**. Un clear aplazado se materializaba después de una copia y borraba el dato recién copiado. Se conserva clear y orden original; no se suprime un draw/clear para ocultar síntoma. Evidencia: suite672/674, dos fallos previos declarados, **sin GPU/gameplay del autor**. No es AMD exclusivo.

**Snap:** `build/source/runtime/vk_exec.c:711–789` emite clear al procesar comando; no aparece Scheduler::deferred_clear. `barrier_to` ordena passes/clear/copy/dispatch. No port aplicable; buen oracle CPU para futuras fusiones de clear: clear→copy→sample debe conservar la copia. No introducir fusión antes de tenerlo.

### 8. Yuzu histórico, preservado en Eden: pitch lineal con origen no cero

[Fix 4c68fc6ea720e2639c57f97bc9228e5de69596ad](https://github.com/eden-emulator/mirror/commit/4c68fc6ea720e2639c57f97bc9228e5de69596ad), 2024-01-31; [merge7e5d50c3806291f167ea29445cb931113c1b5de8](https://github.com/eden-emulator/mirror/commit/7e5d50c3806291f167ea29445cb931113c1b5de8), 2024-02-01, antiguo PR12875. El bucle confundía y0 con número de filas y usaba y absoluto para salida compacta. Separa fila local de `(y+y0)*pitch`. Es corrección matemática de todas las GPUs, **no evidencia de fallo AMD específico**.

**Snap:** `nvn_tex.c:140–143` calcula stride explícito; `vk_exec_xfer.c` tiene caminos de copy región distintos. No usa ese SoftwareBlitEngine. Caso mínimo transferable: ancho3, alto2, x0/y0 no cero, pitch acolchado y sentinelas; comparar roundtrip sin tocar padding. MatyMeatBoy posee el diagnóstico de fotos: trasladar sólo el oracle, no adjudicar causalidad a bandas por semejanza.

## Fuentes negativas que evitan falsos fixes

- [Lichii PR573](https://github.com/zortos293/Lichii/pull/573) está **closed/unmerged**. No usar su merge_commit_sha de prueba como commit integrado. Aubepine sí declara llevarla: su release oficial lo prueba. Las medidas locales del autor son RX9070XT; el cambio combina query-availability, shader específico sin optimizar, lote512 y unswizzle paralelo. Admite que una ganancia previa atribuida al cap de textura era calentamiento de shaders. Ninguna cifra justifica lote512 global en Snap ni lectura de query fabricada como exacta.
- [Lichii PR950](https://github.com/zortos293/Lichii/pull/950), merged2026-11-14 **d58753224d78fb4038989475974ccad2538b0ade**: evita DCC en RADV pre-GFX10. Medido RX580/Mesa26.2.5; no Vega probada, no RDNA2/Windows. Nuestra 6900XT no pertenece al alcance. No desactivar compresión global.
- Mirror Eden PR5 y PR7 están cerradas **sin merge**; no son prueba de solución por el mero cierre. Issue322 cerrado sobre D24 en XC2 tampoco incorpora un fix: el autor lo atribuye al driver.

## Candidato nativo prioritario: CAL y retorno

Fuente primaria [comentario dwk001 del 2026-11-05](https://github.com/Lucas-blip-png/dkb-pc-recomp/issues/45#issuecomment-6646311080) y [revisión del propietario](https://github.com/Lucas-blip-png/dkb-pc-recomp/issues/45#issuecomment-6648101483), búsqueda de `IsUnconditionalBranch` en el registro primario privado. El autor dwk001 documenta una corrección local, no PR merged: excluir InstName.Cal de IsUnconditionalBranch. Prueba declarada del autor en RTX3070Ti Laptop, driver617.42; no transferir el resultado visual a Snap. El propietario retiró después una afirmación de arreglo del crash de cutscene: la pared y la causalidad del crash son evidencias separadas.

Aquí `third_party/astral/tools/vendor/ryujinx/src/Ryujinx.Graphics.Shader/Decoders/Decoder.cs:146–157` registra el callee, pero añade el bloque siguiente solamente si !IsUnconditionalBranch. La función en501–504 devuelve IsUnconditional && Bra sin excepción CAL. Este patrón sí coincide con el reporte; `InstTable.cs:55` confirma CAL con InstProps.Bra | InstProps.NoPred. Falta fixture del decoder real para verificar alcance y retorno en esta revisión.

Experimento mínimo antes de parche: módulo sintético con llamada incondicional, función que retorna, instrucción observable inmediatamente después y llamada predicada de control. Ejecutar decoder real; comprobar sucesores/predecesores y que la instrucción posterior llega al IR/SPIR-V. Control: BRA incondicional debe seguir sin fall-through. Después, probar salida contra intérprete/CPU y spirv-val. No requiere GPU. Si rojo real, cambio mínimo al traductor, regeneración de shaders con identidad nueva; GPU original+AMD sólo después del gate CPU y coordinación. No cambiar sensibilidad, lógica del juego ni precisión matemática para enmascarar NaN.

## Identidad y límites de esta revisión

Árbol NewSnap leído: 8ed155a400ec1475d75659ef50d62f899243944a; donor submodule 248e0b29f308ca84a2d2092019cc60e7fc50ae85. Se contrastó también `build/source/runtime` adaptado existente; no se regeneró ni compiló. Los números de línea de build/source describen ese snapshot local, no una garantía de futuro HEAD. No se ejecutó CPU benchmark ni prueba GPU. No hay prueba física nueva de RX6900XT, ganancia FPS universal ni una corrección de fotos nueva. Las ocho correcciones anteriores son dos linajes principales con forks experimentales, no ocho motores independientes.
