# Inicio y actualizaciones · revisión 0.5

2026-11-13 · trabajo integrado, sin publicar 0.5.

Inicio muestra carga/verificación de GameData, versión, perfil y lanzamiento.
Sin datos, iniciar abre el selector y cancelar conserva Inicio; ya no navega a
Actualizaciones. El constructor no crea GameData ni escanea el álbum. Las
acciones principales permanecen visibles a escala de Windows 125 %.

La revisión independiente detectó y se corrigieron:

- Cerrar una prueba de mando fallida podía liberar el estado ocupado de una
  operación posterior. La ventana ahora libera solo su propia adquisición,
  una vez, incluso ante errores de limpieza.
- Volver a seleccionar GameData sustituía el perfil personalizado por el
  predeterminado. Ahora carga la preferencia de la carpeta seleccionada.
- La falta de bibliotecas de shaders podía bloquear la reconstrucción de un
  runtime antiguo. La comprobación ocurre después de evaluar su reconstrucción.
- Una observación de pantalla caducada dejaba visibles los datos del monitor
  anterior. Ahora se retiran al caducar o cerrar el juego. Un error Vulkan no
  puede validar presentación fija/variable.

Las pruebas de regresión reproducen los fallos sin abrir el juego ni modificar
datos originales. Construcción Tk real y comprobación visual en
`build/launcher-audit-v05/verification.json` y `after-home.jpg`.

Prueba real de red/transacción en
`build/v05-updater-manual-smoke-bb54b438/verification.json`:

- Consulta automática: ninguna estable disponible, sin inventar una estable.
- Catálogo manual: 0.4, 0.3 y 0.2 alpha publicadas con launcher verificable.
- Descarga real 0.4 desde el repositorio, checksum y manifiesto verificados.
- Instalación y reinstalación de la misma versión en carpeta aislada.
- 1102 archivos instalados; conservados sentinelas de GameData/perfil/guardado
  y preferencias del launcher. Ningún dato real del propietario modificado.

No equivale a una entrega 0.5 ni a validación física de mando/AMD. La prueba de
instalación ejercita la API del updater; el reinicio del ejecutable congelado se
volverá a comprobar al empaquetar el candidato final.

El launcher de desarrollo también fue congelado y su `--selftest-launcher`
terminó con código 0 usando un PATH sin Python instalado. Los fingerprints de
fuentes coinciden y el PNG de mando incluido conserva el SHA original. Evidencia:
`build/launcher-audit-v05/frozen-verification.json`. No se publicó este ejecutable;
su identidad continúa en 0.4 mientras la puerta de salida 0.5 permanece abierta.

La prueba visual del mando, con entradas sintéticas y sin sensores físicos, está
en `build/launcher-audit-v05/controller-switch-after.jpg`. La selección entre
mandos, desconexión y liberación exclusiva del estado ocupado tienen regresiones.
