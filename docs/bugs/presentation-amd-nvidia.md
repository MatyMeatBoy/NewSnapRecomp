# Suavidad de presentación: RX 6900 XT y RTX 4060

Estado: abierto, asociado a PACE-01 / QA-AMD-01. Reporte del propietario del
13/11/2026: la prueba local se siente distinta al ZIP de GitHub ejecutado en la
RX 6900 XT con monitor FreeSync. Astral Chain es su referencia de suavidad.

## Lo comprobado en código y capturas

- El launcher tiene `mailbox` como valor inicial; la captura AMD muestra VSync.
  No son prueba de una configuración ni una presentación efectiva idénticas.
- `vrr_adapt.py` consulta y publica estado cuando la extensión está disponible;
  no cambia la política de colas ni activa FreeSync por sí mismo. El nombre
  VSync del HUD tampoco certifica VRR activo en el monitor.
- El pacer heredado calcula slots y disponibilidad en `nvn_api_obj.c`; el overlay
  de Snap conserva el intervalo original y aplica el límite del host sin usar
  los parches de simulación específicos de Astral Chain.
- Un promedio de 60 FPS o un intervalo de 16,7 ms no identifica duplicados,
  fotogramas perdidos ni la cadencia real de salida del compositor/monitor.

## Comparación necesaria para cerrar

Usar el mismo recorrido, versión de runtime identificada automáticamente,
resolución, escala, preset nativo, estado de caché y límite en ambos equipos.
Registrar modo solicitado y efectivo de swapchain, monitor/refresco, estado VRR
observado o desconocido, modo ventana/pantalla completa y cambios de monitor.
Comparar FIFO/mailbox donde estén soportados, sin cambiar simultáneamente otros
ajustes. Conservar p50/p95/p99, máximo y número/duración de picos del host;
complementar con tiempos de presentación observados cuando estén disponibles.
Separar trabajo CPU/GPU, espera del pacer, bloqueo de acquire/present y cargas.

La cabeza de la intro tiene tarea independiente HEAD-INTRO: un defecto localizado
de animación no queda explicado por un pico global sin correlación de evidencia.
No copiar direcciones/parches de animación de Astral Chain ni alterar velocidad,
lógica, fotogramas de simulación o colores para disimular diferencias.

No se ha ejecutado una comparación física AMD/NVIDIA en esta revisión. No
declarar mejorada la suavidad AMD hasta disponer de una medición comparable y
confirmación del propietario. Las pruebas GPU del checkout se serializan con
las reproducciones de teclado/fotos en curso.
