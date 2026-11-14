# Correcciones portables posteriores a 0.5 alpha

Integradas en main: `47be383`. No modifica los assets publicados de 0.5 alpha.
El ZIP que probó el propietario sigue siendo el publicado, todavía sin estas
correcciones. La siguiente entrega necesita freeze, kit exacto y validación del
paquete completo en una instalación sin credenciales de GitHub.

## Causa y cambios

La reconstrucción desde el launcher descargaba el kit al necesitar un runtime
compatible. El repositorio privado responde 404 sin acceso; el PC de desarrollo
autenticado no cubría ese caso. El paquete Windows ahora exige e incluye el kit
público exacto (versión, revisión completa, API, capacidades, donante, inventario
y hashes). El cliente verifica tamaño/hash fijados en MANIFEST antes de extraer
el kit local en su caché propia; con el bundle válido no consulta GitHub.
Sin bundle mantiene la descarga verificada y explica el 404. No se incluyen
credenciales ni se fuerza la ejecución de un runtime incompatible.

La detección prioriza imports completos frente a selecciones antiguas ausentes
y carpetas solo con marcador. Revisa únicamente layouts conocidos directos,
anidados y vecinos; no recorre el disco ni cambia la preferencia guardada.
Una instalación inexistente no adopta los datos de su padre. La presencia no
sustituye la verificación de los datos originales.

Se ocultan las consolas de productores Python/Ninja redirigidos y helpers
nativos. Reexec/restart conservan una consola explícita de uso CLI y permanecen
sin consola cuando el launcher no tiene una. Se conservan pipes, salida,
códigos de retorno, suspensión, Job y cancelación. No se cierran CMD ajenos.

## Verificación y límites

72 pruebas dirigidas pasan: adquisición local/remota, rechazo de bundle roto o
sin pin, cancelación, 404, empaquetado público, descubrimiento, mantenimiento,
procesos nativos y aplicación conjunta de overlays. Evidencia privada:
`build/launcher-portable-final.log`. Revisión independiente del bundle sin
bloqueos nuevos. No es una confirmación física de RX 6900 XT ni del nuevo EXE.

Pendiente P2 preexistente: una caché local corrupta se rechaza antes de intentar
usar el bundle válido. La recuperación debe aislar únicamente esa generación
de caché y verificar otra extracción; nunca borrar imports o runtime del usuario.
