# Matriz de evidencia gráfica y de entrada · 0.5

Fecha: 2026-11-13. Documento de revisión; no autoriza publicación de 0.5 ni
cambia el estado de aceptación del propietario. La release 0.4 es inmutable.

## Cómo interpretar los estados

- **Observado**: resultado registrado en una ejecución/captura identificada.
- **Inferido**: explicación plausible que todavía requiere el control causal.
- **Corregido en código**: cambio implementado; no equivale a validación física.
- **Verificado CPU**: funciones nativas reales con dependencias controladas.
- **Verificado GPU**: solo el dispositivo, binario, modo y recorrido indicados.
- **Pendiente**: falta ese ensayo; no se sustituye por otra GPU o un fixture.

El equipo local es **NVIDIA GeForce RTX 4060 Laptop GPU**; el A/B normal registra
driver **616.92**. El propietario reportó fallos en **AMD RX 6900 XT**, modo
**Original**, monitor FreeSync. No inferir un driver AMD, estado HDR o VRR real
sin su registro. Otros modelos de GPU no están validados por estos resultados.

## Contratos y cobertura

| Contrato | Causa/estado del cambio | CPU/control nativo | RTX 4060 local | RX 6900 XT del propietario |
| --- | --- | --- | --- | --- |
| Color SDR de presentación | **Corregido**: el formato base sRGB no describe por sí solo la transferencia usada al escribir los bytes finales. Elegir vista compatible según fuente **y destino**, sin tocar el grade del juego. | Matriz RGBA/BGRA × UNORM/sRGB; pares equivalentes sin copia, float/desconocidos conservan semántica. | **Observado**: a 1920×1080 exactos, `f01114` frente a presentación tiene MAE=0 y máximo=0 en `v05-final-color-coherence-1to1`. Binario `f6d92250…`. Los cuadros vecinos difieren temporalmente; no todos son coincidencias exactas. | **Pendiente**: la sobresaturación/contraste reportados no quedan físicamente corregidos por una comparación NVIDIA. |
| Importación de memoria host | **Corregido**: la selección del donor puede devolver un tipo compatible que no cumple las propiedades solicitadas. La ruta de importación directa requiere `HOST_VISIBLE` y `HOST_COHERENT`; sin ambas elige almacenamiento gestionado existente. Sus rutas de flush/barreras/fences se auditaron en fuente; no se validó ese fallback en GPU. Sin excepción por vendor. | Negativo: tipo visible/cacheado no coherente elegido por el selector anterior. Positivos: flags elegidos, import coherente conservado, fallback por pool/tracking y llamada invalidate controlada. `shadow_sync_pool` es un stub contador: no prueba flush, visibilidad GPU ni finalización. | **Observado**: ensayo final normal registra tipo 2, propiedades `0x6` (visible/coherente), conservando la ruta directa. No ejecuta ni valida el fallback físico de AMD. | **Pendiente**: ni el tipo de memoria realmente seleccionado ni la causa de sus franjas están establecidos con bytes/traza AMD. |
| Dibujos gráficos con escrituras storage | **Corregido**: omitir por pipeline pendiente un draw con SSBO escrito/image store omite una operación funcional, aunque su render target sea reciente. Se espera traducción/reflection y pipeline para esos efectos. | Donor falla el negativo; pruebas VS/PS, SSBO/image store, lectura sola, traducción desconocida, varias esperas y fallo real. | Runtime integrado `06a8d9df…` compilado y ejecutado en A/B normal; ese recorrido caliente no tuvo skips. Eso no demuestra qué draw causaba las franjas/retícula. | **Pendiente**: la reflexión local de un shader con storage demuestra uso de la clase, no causalidad del reporte AMD. |
| Dispatch compute | **Observado en fuente**: `op_dispatch`/`op_dispatch_ind` solicitan traducción sin pending y pipeline compute síncrono. | Hipótesis de que pasan por el skip gráfico **descartada**. No se añadió un parche compute basado en esa suposición. | No es una aceptación independiente de todos los dispatches. | Sin ensayo específico; no atribuir el defecto a compute por el aspecto de las bandas. |
| Captura → buffer → JPEG → miniatura → evaluación | Diagnóstico opt-in acotado compara transferencias conservando pitch/formato/lifetime. La lógica original de selección/evaluación/tutorial se mantiene. | Fixtures instrumentan transferencias reales con APIs controladas; auditoría CPU independiente del banco/JPEG tiene su propia revisión pendiente. | **Observado**: controles normales separados de 540 s con `f6d92250…` y `06a8d9df…`, cada uno exit 0, dos fotos nuevas y dos miniaturas sin filas negras, cuatro transferencias GPU fuente/buffer idénticas y progreso de tutorial registrado. El anterior además identifica captura de primera expedición. La evidencia final es propia, no heredada del anterior. | **Pendiente**: captura del propietario muestra franjas y rechazo de selección; no prueba que las franjas causen ese rechazo ni dónde nacen. Faltan bytes AMD. |
| Ratón, foco y sensores | **Corregido**: epoch de captura; reinicio de fusión al cambiar/perder fuente; no habilitar sensores con movimiento apagado; rollback parcial; eliminar caché compartida no atómica del ajuste live. | 19 escenarios nativos; donor presenta once fallos. Dos hilos Win32 reproducen lectura vieja que contaminaba el ajuste nuevo. Tres unidades completas pasan sintaxis. | Binario integrado compilado; fixtures no activan hardware. No equivalen a aceptación del mouse/mando físico. | **Pendiente**: la cámara que apunta sola puede tener otras causas, incluido drift físico no medido. No alterar sensibilidad/deadzone para ocultarlo. |
| VRR | La sonda separa observación/capacidad/estado desconocido. FIFO/mailbox no certifican VRR. | Contratos y parser específicos, separados del hardware. | A/B usó mailbox y swapchain 1920×1055; eso **no demuestra VRR**. | FreeSync del monitor es contexto del reporte, no una medición de cadencia variable del swapchain. |

## Evidencia local reproducible

Los enlaces bajo `build/` apuntan a artefactos privados ya existentes. No subir
capturas, fotos, partidas, imports, claves, cachés derivadas o ejecutables.

| Evidencia | Alcance y límite |
| --- | --- |
| `build/v05-original-color-fixed-1to1/pixel-comparison.json` | Primer par digital exacto `f01108`: MAE/máximo/RMS=0; decodificación sRGB incorrecta ≈49,47 MAE. |
| `build/v05-final-color-coherence-1to1/{run.json,pixel-comparison.json}` | Corrección con matriz fuente/destino; mejor par `f01114`, 1920×1080, MAE/máximo=0, binario `f6d92250c57917e37ac8ab0bfc02792896feeb56df69ccceca6265019f034eba`. No es una validación física HDR ni fallback sRGB-only. |
| `build/v05-import-coherence-proof/proof.c` | Prueba mínima del selector que acepta tipo no coherente; complementar con `tests/test_photo_readback.py` y el adaptador, no confundir con traza AMD. |
| [Efectos gráficos](graphics-side-effects.md) | Causa, cambios, negativo/positivo y límites de `tests/test_graphics_effects.py`. |
| `build/v05-positive-control-normal540/{run.json,photo-evidence.json}` | Binario `f6d92250…`, exit 0, frame final 32272; fotos 1080×720, miniaturas 240×200. Las copias `save`/`save-tx` no son fotos independientes. Hubo actividad async real: no confundir con un benchmark caliente sin skips. |
| `build/v05-final-positive-control-normal540/{run.json,photo-evidence.json}` | Ensayo distinto con binario `06a8d9dfee5d8ee5c6d3cfe72beccf3d4e5d3f1d553ea7187cd7231be52b722d`: exit 0, frame final 32252, originales/perfil/backups intactos, cuatro transferencias con cero diferencias y dos fotos/dos miniaturas nuevas sin filas negras. Registra 98 skips de pipeline pendiente y cero skips por traducción shader; no prueba que se omitiera un draw con efectos storage. PyInstaller/tests concurrentes: no es benchmark limpio. |
| [Auditoría de bancos](photo-bands-cpu.md), [revisión](photo-audit-review.md) | Los 150 bancos históricos contienen duplicados: solo dos fotos únicas de una ruta. Un parser/veredicto de auditoría también necesita pruebas de daños y protección de fuentes. |
| [Entrada](camera-input.md), `build/v05-camera-input-results.json` | CPU/threads y compilación; aceptación física pendiente. |

## Rendimiento: resultados separados

[El A/B normal](../../build/v05-normal-pacing-ab/REPORT.md) compara una corrida
medida de 40 s por binario, cada una tras 40 s de calentamiento, con GPU
serializada, mismo seed de perfil/caché, Original, cap 60, render 100 % y mismo
swapchain efectivo 1920×1055. No utiliza `--shot` ni capturas de vuelo activas.

| Intervalo de juego completo | 0.4 | Integrado `06a8d9df…` |
| --- | ---: | ---: |
| Muestras | 2355 | 2354 |
| Media, ms | 17,003 | 17,004 |
| p50, ms | 16,654 | 16,662 |
| p95, ms | 19,661 | 19,301 |
| p99, ms | 34,781 | 42,523 |
| Máximo, ms | 104,370 | 110,373 |

**No hay ganancia global de pacing demostrada.** Media/mediana son equivalentes
y las colas son mixtas. El segmento posterior mejora algunas colas, pero no
reemplaza el resultado completo. Cero traducciones/skips/esperas runtime en esta
ventana no atribuye los picos restantes a un mecanismo concreto. Inicio/prewarm
se mide por separado; una única corrida no establece repetibilidad ni regresión
causal. Las corridas fotográficas tuvieron concurrencia CPU declarada y no sirven
como comparación limpia de pacing.

La caché de generación es otro coste: `build/v05-generation-cache-real/evidence.json`
registra generación + recibo **86,820 s**, publicación **3,351 s**, restauración
**3,044 s** y verificación **0,265 s**; 150 salidas/287.542.127 bytes idénticos,
copias independientes y misma ruta owner. Se verificaron originales en ambos
recorridos. No se compiló código nativo ni se usó GPU en ese ensayo: **no mide FPS**.

## Puertas pendientes

Conservar pendientes AMD, aceptación física de entrada, retícula/foco y escenarios
fotográficos no cubiertos. El ensayo final de 540 s aporta aceptación local
acotada de esa ruta; un fixture verde o una corrección de contrato no permite
marcar resuelto todo el reporte.
No saltar validaciones, cambiar flags de progreso ni fabricar puntuaciones.
