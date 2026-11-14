# Reportes del propietario tras publicar 0.5 alpha

Equipo confirmado por el propietario: RX 6900 XT. Usa el ZIP público 0.5 de
GitHub, no el paquete privado dev1. La versión/hash del ejecutable realmente
iniciado todavía debe vincularse: hay error 404 del launcher y lanzamiento forzado.
No asumir que la versión del launcher certifica la del runtime.

## Pendientes críticos y reparto

| ID | Observación concreta | Trabajo siguiente |
| --- | --- | --- |
| LAUNCH-404 | Correr devuelve 404 y debe forzarse el inicio. | Codex: adquisición/kit local/autenticación del repo privado, sin saltar validaciones. |
| AUTO-DATA | GameData está en la carpeta del port y no se detecta automáticamente. | Codex: rutas portables, preferencias antiguas y presencia sin marcador. |
| FOTO-01/02 | Selección: foto grande y ambas miniaturas tienen bandas negras. Evaluación posterior: una foto de Pikachu sí se ve completa. | Codex/Claude: comparar rutas, slots, buffers y JPEG guardado. La vista correcta no prueba que todos los bytes persistidos sean válidos. |
| KEYBOARD-CRASH | Justo después del registro/evaluación mostrados, abre el teclado de Windows y el juego se cierra. | **Libre para Claude**: applet/entrada de nombre/callback/retorno; distinguir excepción de salida normal con los logs. No omitir pasos del juego. |
| COLOR-01 | El propietario sigue viendo los colores excesivamente saturados. | Verificar runtime, datos/configuración efectiva y transferencia en AMD; no compensar alterando el grade del juego. |
| HEAD-INTRO | Stutter localizado en la cabeza al entrar caminando antes del logo. | **Libre para Claude**: analizar animación/transformaciones y cadencia; no atribuirlo sin prueba al pacing general. |
| CONSOLE-01 | Sigue un CMD corriendo en segundo plano. | Codex: identificar proceso propio/origen y flags de creación; conservar diagnóstico. |
| HOME-PROFILE | Solicita quitar «Elegir perfil» de Home. | Codex: mover la selección avanzada a Opciones, conservar perfil y defaults. |

El repo es privado (consulta de GitHub confirmada). Que una descarga funcione en
el PC de desarrollo con gh autenticado no acredita un PC sin esas credenciales.
No incluir tokens/credenciales en paquetes ni cambiar visibilidad del repo.

El propietario también observa diferente suavidad entre la prueba local y la
6900 XT/FreeSync; Astral Chain es su referencia. Seguimiento y comparación:
`docs/bugs/presentation-amd-nvidia.md`. Comparar cadencia efectiva, no solo FPS.

## Capturas y límites de inferencia

Copias privadas en `build/user-reports/rx6900xt-0.5/`, con SHA256 y ruta original
en `evidence.json`: `album-bands-amd.png` y `evaluation-good-amd.png`. No subir las
imágenes, bancos, fotos ni otros datos del juego a GitHub.

El HUD muestra RX 6900 XT / i9-10850K, ventana 2560×1440, imagen 1920×1080,
escena 1600×900 y «AMD FSR 1, sharpness 80%». Es una pista para identificar
runtime/configuración efectivos; no demuestra por sí sola qué versión ejecutó
ni que ese filtro explique las bandas. No declarar las fotos arregladas por la
imagen correcta de una sola pantalla.

**Confirmación positiva independiente:** el propietario dice que el cuadrado de
foto ya se ve bien en la 6900 XT. Eso cierra el defecto visual reportado de ese
recuadro; no cierra fotos guardadas, color, animación ni teclado.

Pudo seleccionar las carpetas de Pikachu/Vivillon y avanzar. No recuperar el
perfil anterior: el propietario lo excluyó expresamente. Mantener la lógica de
sujetos, evaluación, tutorial y guardados; no fabricar progresos o puntuaciones.

Tomar tareas y reservar archivos en `docs/PENDIENTES.md` antes de editar. Entregar
PR temático desde worktree aislado; Codex integra y prueba. La release 0.5 alpha
publicada permanece inmutable; estas observaciones reabren los casos afectados.
