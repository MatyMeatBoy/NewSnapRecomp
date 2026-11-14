# Recuperación del kit e identidad de sesión

## Fallos reproducidos y correcciones

Un caché con una herramienta dañada se rechazaba antes de intentar el bundle
válido. Ahora solo un fallo de integridad inicia recuperación local: se verifica
el bundle exacto, se extrae/verifica el candidato completo y se serializa su
publicación mediante lock del sistema operativo. El caché fallido queda en una
cuarentena propia. Cancelación/permisos no se convierten en una descarga ni se
modifican imports/perfiles; un fallo de publicación restaura el slot anterior.
Una revisión independiente y pruebas de rollback/publicación simultánea pasan.
Las cuarentenas se conservan para diagnóstico, sin limpieza automática.

Los logs de lanzamientos anteriores no permitían contrastar automáticamente el
ejecutable con la versión del launcher. Cada intento nuevo registra su SHA256
leído, claims del marcador separados, discrepancia si existe y exit code real.
El hash se calcula en el worker, no en Tk. Una afirmación del marcador no
sustituye ese hash. Mayúsculas hex válidas no producen discrepancias falsas.

El triaje CPU del PR #2 se integra por separado del overlay de applets, todavía
en revisión. Reconoce nombres nuevos/legados, conserva clasificación y marca la
generación como inferencia del log. Se endurecieron rutas con espacios y JSON
anidado/corrupto; datos de identidad aceptados son escalares acotados. El ZIP
incluye análisis JSON legible por sesión, además de texto redactado y resumen.
No requiere ejecutar agentes, red ni utilidades externas en el PC de prueba.

## Evidencia y límites

387 pruebas completas antes de la nueva identidad, una omitida por privilegios
symlink; las comprobaciones de reparse attributes se ejecutan. Evidencia privada:
build/pending-investigation-full.log, portable-observability-reviewed.log,
diagnostics-reviewed-final.log. El rechazo de un caché sin bundle se conserva;
no se usan kits de versiones/revisiones distintas para rescatarlo.

El runtime 8ff756d se compiló desde cero y pasó selftest/loader. Prueba Vulkan
aislada RTX de 20 segundos: salida 0, boot passed, INI legado intacto; SHA256
d733b8c8d805fd73a523e297b520347752b017afef2d85c228137adfd2ef6968.
La caché fría muestra picos con traducción de shaders, incluido 685,5 ms con
593,3 ms de traducción agregada; los contadores se solapan y no deben sumarse.
Esto no explica por sí solo el pico previo de 107 ms ni verifica fotos/AMD.

La compilación y prueba anteriores no incluyen las nuevas trazas de presentación
y pool; necesitan su verificación integrada y entrega con identidad propia.
