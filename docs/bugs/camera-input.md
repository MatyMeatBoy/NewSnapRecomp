# INPUT-01 · Continuidad de cámara y sensores

Estado: propuesta para revisión independiente. Responsable: Codex, 2026-11-13.

## Causas reproducidas en funciones del donor

1. `mouse_camera` conserva `held[2]` durante el mismo frame presentado. Los
   backends borran los deltas del ratón al recapturar, pero el consumidor no sabe
   que hubo una liberación/recaptura si ambas ocurrieron entre dos lecturas del
   juego. Reutiliza entonces la inclinación anterior, aunque el ratón esté quieto.
2. `motion_main` llama `sensors_ready` antes de comprobar `AC_MOTION`. Por tanto
   puede encender sensores con movimiento desactivado. Si se habilita gyro y
   falla habilitar acelerómetro, deja el gyro habilitado parcialmente.
3. Desconectar/cambiar mando, desactivar movimiento o perder una lectura no
   reinicia la fusión. El anillo conserva muestras hasta 200 ms y un mando nuevo
   hereda ángulo/orientación anteriores. No es una calibración incorrecta del
   sensor: el fixture reproduce el defecto con muestras sintéticas exactas.
4. `input_motion_enabled` duplica la caché de configuración con dos estáticos
   no sincronizados (`on`, `seen`) compartidos entre el hilo gyro y lectores del
   juego. Una lectura antigua pausada puede terminar después de una lectura de
   la nueva configuración y dejar `on` antiguo con `seen` nuevo: el movimiento
   queda habilitado aunque la configuración vigente diga apagado.

Estas causas están verificadas en CPU; no se ha atribuido causalmente a ellas
la cámara del propietario. El drift físico del gyro o un stick fuera de su zona
muerta configurada todavía requieren evidencia de su dispositivo.

## Corrección propuesta

`newsnap/camera_input_adapt.py` añade ediciones puntuales:

- Los backends Win32 y SDL cuentan cada transición efectiva de captura; la
  cámara invalida su muestra retenida cuando cambia ese contador, incluso sin
  cambiar el frame. La acumulación/conversión original de movimiento se conserva.
- El sondeo comprueba `AC_MOTION` antes de habilitar/leer sensores. Al apagarlo,
  deshabilita los sensores previamente iniciados. Una habilitación parcial se
  revierte.
- La fusión real se reinicia al perder/cambiar fuente, tras cerrar/reabrir el
  mismo identificador y cuando falla una lectura que seguía a muestras válidas.
  La lectura siguiente empieza una referencia nueva; no integra a través de esa
  discontinuidad. El cambio se observa en el siguiente sondeo de 4 ms.
- `input_motion_enabled` consulta directamente `cfg_bool`, cuya publicación ya
  es atómica, sin añadir una segunda caché compartida que pueda quedar obsoleta.

No se modifican sensibilidad, defaults, zonas muertas, ejes, simulación ni
algoritmo de fusión. El mando conserva su comportamiento de entrada en segundo
plano; la corrección de ratón sigue las transiciones del cursor.

## Pruebas y evidencia

```
.venv\Scripts\python -X utf8 -m unittest tests.test_camera_input -v
```

Seis pruebas compilan/ejecutan las funciones C reales con APIs de plataforma/SDL
simuladas. Incluyen ambos backends de captura, recaptura sin cambio de frame,
reposo inicial, retención legítima dentro del frame, siguiente frame quieto,
liberación y frame detenido; movimiento apagado desde inicio, apagar/encender,
desconectar/reconectar, cambiar mando, reabrir mismo ID, fallo parcial de sensores,
fallo de lectura, reposo y giro continuo; y zona muerta original con stick neutro,
ruido dentro de la zona configurada y entrada deliberada de amplitud completa.
La fusión procede íntegra de `motion_fusion.c`, no de una reimplementación Python.
Una prueba adicional usa dos hilos Win32 reales y eventos para detener una lectura
vieja, aplicar/apagar y leer el ajuste nuevo, y después completar la lectura vieja;
la llamada posterior debe seguir devolviendo apagado. El donor falla exactamente
en esa última comprobación. Los sensores siguen simulados y no se inicia SDL.
También se verifica sintaxis de `input.c`, `input_win.c` e `input_sdl.c` completos
con headers SDL/Vulkan/Win32 del toolchain.

`NEWSNAP_INPUT_BASELINE=1` omite el adaptador en las mismas pruebas: once
subcasos fallan sobre el donor. Con el adaptador pasan. Logs locales:
`build/v05-camera-input-red.txt` y `build/v05-camera-input-green.txt`.

No se inició SDL real, ningún sensor/vibración físico, juego ni prueba GPU.
Tampoco se modificaron datos o configuración del propietario.

## Integración y límites

El coordinador incorporó `camera_input_adapt.edits` a `newsnap/adapt.py` y
compiló el runtime integrado `06a8d9df…`. La revisión independiente de locks,
captura y ciclo de sensores aprobó los cambios; su observación sobre la caché
compartida de `input_motion_enabled` también se corrigió con una regresión de
dos hilos reales. Queda pendiente la aceptación con el mouse/mando físico del
propietario. No atribuir el caso del propietario solo por pasar los fixtures.
