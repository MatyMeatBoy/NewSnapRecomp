# FOTO-01: límites de imágenes enlazadas al pool

La hipótesis de franjas AMD sigue sin confirmar. Un fixture CPU ejecutando
`bind_pool_memory` del donor demuestra que puede admitir dos imágenes de color
cuyos requisitos Vulkan se solapan aunque sus almacenamientos NVN sean contiguos:
imagen A: rango NVN `[0,64)`, Vulkan `[0,128)`; imagen B: NVN y Vulkan `[64,128)`.
La resolución comprueba el pool físico o tramo virtual contiguo completo, no
las subasignaciones de cada textura. Profundidad/stencil ya rechaza el exceso.
Esto prueba una condición admitida por el código; no prueba que un controlador
AMD produzca esos requisitos, escriba el exceso o cause las fotos del usuario.
Una geometría repetible tampoco descarta trabajo parcial o carreras repetibles.

`newsnap/pool_bounds_adapt.py` proporciona un experimento sin selección por GPU.
El integrador debe conectarlo a `adapt.py`; este módulo no se activa por sí solo.

- Sin flag, conserva las decisiones del donor y registra las primeras 16
  imágenes de color y 4 de profundidad/stencil por proceso con
  `req.size > guest_size`, incluyendo rechazos. Los presupuestos separados
  impiden que los rechazos de profundidad consuman la evidencia de color.
- `AC_SNAP_POOL_BOUNDS=1` rechaza también imágenes de color con ese exceso.
  La creación usa entonces su alternativa existente de memoria propia VMA.
- Otros valores conservan la política original. El flag se memoriza en el
  primer candidato de color con exceso mediante publicación atómica; se debe
  fijar antes de iniciar el proceso, no cambiar durante la sesión.
- No añade consultas Vulkan, lecturas del contenido guest ni instrumentación
  por frame. Los contadores atómicos permiten un máximo total de 20 líneas,
  incluso con concurrencia.

Cada línea `pool_bounds:` incluye handle/dirección, formatos NVN/Vulkan,
dimensiones NVN, tamaño guest/requerido, alineación, tipos compatibles,
tipo de memoria seleccionado y offset/tramo disponible si llegó a resolverse.
`span_known=0` significa que los ceros de offset/tramo no son una observación.
`decision` identifica la salida real; `bound=1` solo aparece tras un bind exitoso.
Los logs no indican qué bytes del rango utiliza internamente el controlador ni
demuestran que otra textura esté viva allí. El presupuesto puede agotarse antes
de la foto; ausencia de líneas posteriores no significa ausencia de exceso.

La alternativa VMA no garantiza una asignación `VkDeviceMemory` dedicada.
Aumenta `own_bytes`, participa en el presupuesto y la expulsión del caché y
puede limpiar a cero la imagen al inicializarla. También pierde el alias implícito
con el buffer del pool u otras imágenes. `alias_copy` conserva ciertos aliases
compatibles de la misma dirección base mediante staging, no todos los aliases
parciales o con otras bases. Por eso el flag es experimental y está desactivado
por defecto; no constituye una corrección AMD aceptada.

Las reglas Vulkan sobre rangos solapados no garantizan conservar el contenido
de imágenes no lineales por el mero hecho de compartir memoria. Referencia:
[Memory Aliasing de Vulkan](https://docs.vulkan.org/spec/latest/chapters/resources.html#resources-memory-aliasing).

Prueba focalizada: `python -m unittest tests.test_pool_bounds -v`. Compila y
ejecuta la función C adaptada con Vulkan/VMA simulados: default/opt-in,
profundidad/stencil, tamaño cero/justo, resolución, alineación, tipo, fallo de
bind, orden/número de llamadas y límite concurrente de logs. No simula un
controlador GPU ni mide imágenes reales. Faltan compilación nativa integrada,
control RTX y A/B de la misma ruta en AMD con identidad verificada.
