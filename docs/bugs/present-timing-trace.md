# Trace optativo de esperas de presentación

La evidencia AMD recibida pidió mailbox pero obtuvo FIFO; el A/B local NVIDIA
obtuvo mailbox. Los contadores existentes juntan esperas de fences y drenaje de
replay y pueden sumar intervalos de varios hilos. No permiten atribuir un tirón
concreto a adquisición, presentación, GPU o reconstrucción del swapchain.

`AC_SNAP_PRESENT_TRACE=1` habilita observaciones por proceso. Se lee una sola vez
mediante el constructor del runtime, antes de arrancar hilos; cualquier otro
valor lo deja apagado. No es una preferencia INI ni una política de sincronización.
El launcher puede pasarlo explícitamente al proceso de una prueba. Este cambio no
modifica el launcher ni activa el flag por defecto.

## Qué mide

El adaptador `present_trace_adapt.py` usa once anclas exactas de
`runtime/gfx_present.c`. La pareja `plat_now_ns()` rodea las operaciones reales:

- `acquire`: cada `vkAcquireNextImageKHR`, incluido el reintento posterior a
  `VK_ERROR_OUT_OF_DATE_KHR`.
- `fence`: la espera previa al slot y la espera adicional usada al capturar. Ambas
  se agregan en la misma categoría; para comparar pacing, no tomar capturas.
- `queue_present`: `vkQueuePresentKHR`. El intervalo excluye adquirir/liberar el
  queue lock; el log se escribe después de liberarlo.
- `rebuild`: toda la función existente de creación/reconstrucción, desde su
  entrada hasta cada retorno, incluidos el flush pendiente, consultas, espera
  device-idle y creación/liberación de recursos. Su resultado es el booleano
  original, no un `VkResult`. La duración puede incluir una llamada de presentación
  también medida aparte: **no sumar las categorías como tiempos exclusivos**.

Las líneas `snap_present_trace: operation=...` contienen conteo, suma, mínimo y
máximo en nanosegundos, número de resultados distintos del éxito y resultado de
la última muestra. Para Vulkan, éxito significa `VK_SUCCESS` (0); `SUBOPTIMAL`,
timeout y demás resultados cuentan como `other_results`, sin confundirlos todos
con fallos fatales. Para rebuild, éxito significa 1. Los contadores son acumulados
desde el inicio del proceso, no percentiles ni una ventana deslizante.

Se emite la primera muestra de cada categoría. Después, como máximo una línea
por segundo y categoría, tras unas 120 llamadas; a 60 FPS son unos dos segundos.
Las reconstrucciones poco frecuentes no esperan 120 llamadas, pero conservan el
límite de un segundo. Las muestras finales que no alcanzan el siguiente umbral
no se vuelcan al cerrar. El almacenamiento es fijo: cuatro buckets, sin listas
de frames, hilos auxiliares ni archivos nuevos.

Una línea de swapchain informa modo solicitado/efectivo, modos enumerados como
valores Vulkan, cantidad reportada/capturada, resultado de esa consulta, imágenes
solicitadas/reales, resultado de consulta de imágenes y extensión. Reutiliza las
consultas que el donor ya ejecuta; no añade consultas GPU. La enumeración conserva
el límite existente de 16 modos. Si la consulta de imágenes no termina con éxito,
`images_actual=0` significa desconocido. Estos snapshots tienen límite de una
línea por segundo: no constituyen un historial exhaustivo de cambios rápidos.
No se deduce VRR, FreeSync, soporte del monitor ni presentación física de FIFO,
mailbox, tiempos CPU o número de imágenes.

## Contrato sin alteración de política

Apagado, los wrappers solo comprueban el flag y no llaman al reloj, al logger ni
a las funciones de agregación. No se cambian timeouts, reintentos, resultados,
conteos de imágenes usados por el donor, prioridades, sleeps, cap, colas ni el
orden de las llamadas Vulkan. Todos los puntos están serializados por el
`g_pl` existente; el helper no añade locks. El flag se inicializa antes de los
hilos y nunca se modifica en vivo. Las atribuciones y el donor original quedan
intactos.

`python -m unittest tests.test_present_trace` ejecuta tres pruebas CPU:

- Fixture nativa del helper: opt-in exacto, cero consultas temporales/logs al
  apagarlo, agregados conocidos, resultados Vulkan negativos/positivos, conteo
  booleano de rebuild y límites de emisión.
- Anclas sobre el donor real: ambas adquisiciones y fences siguen presentes,
  sin duplicar llamadas ni cambiar las condiciones de salida/reintento.
- Funciones reales adaptadas de selección de modo, flip y wrapper de rebuild con
  Vulkan simulado: conservan fallback, orden del lock, códigos/dirty flags y
  retornos tanto apagado como encendido. La prueba del present añade tiempo al
  unlock deliberadamente y comprueba que queda fuera del intervalo medido.

Antes de implementar fallaron el opt-in y la ausencia de los seams. Las tres
pruebas pasan tras el cambio. No se ejecuta GPU ni juego. Falta integración del
coordinador, `adapt_sources` completo, compilación y ensayo GPU serializado.

## Experimento mínimo posterior

Usar el mismo binario, recorrido corto conocido, resolución, estado de caché y
perfil copiado. Bloquear un modo efectivo soportado durante cada corrida, sin
cambiarlo en vivo ni capturar frames. Registrar drivers y modo solicitado/real.
Comparar adquisición, fence, queue-present y reconstrucciones por separado junto
con frametimes existentes; los valores acumulados permiten diferencias de
conteo/suma, pero sus máximos no son p99. Exigir mejoras repetibles de colas sin
errores, cambios de cadencia del juego ni regresión de fotografías. El trace tiene
coste diagnóstico cuando está encendido: no presentar su resultado como un
benchmark limpio ni como validación AMD por haberlo probado en NVIDIA.
