# Aceptación del candidato 0.5 en RX 6900 XT

La versión 0.5 sigue en desarrollo. Las pruebas RTX 4060 son controles locales;
no cierran los defectos observados por el propietario en AMD. No publicar hasta
completar las puertas de `docs/PENDIENTES.md`.

## Preparación

- Usar una copia completa de la carpeta portable y de GameData. Conservar la
  instalación 0.4 y su perfil originales sin cambios. No mezclar un ejecutable
  candidato con el marcador o launcher de una receta distinta.
- Antes de lanzar, comprobar en Home que datos y perfil apuntan a esa copia.
  `launcher.json` puede conservar un perfil absoluto externo; usar «Elegir
  perfil» para seleccionar el perfil copiado y confirmar la ruta mostrada.
- Registrar SHA256 del ejecutable, revisión del candidato, versión del driver
  AMD, resolución, escala de Windows, modo de pantalla y estado HDR/FreeSync.
- Comenzar en Original, escala 100 %, modo TV, límite 60 FPS y movimiento
  desactivado. Estos ajustes aíslan los fallos reportados; después se prueban
  por separado las otras opciones. No alterar saturación, contraste ni gamma.
- Preparar shaders para esa GPU mediante el launcher. Conservar su registro.
  Separar el arranque/preparación de la medición con caché caliente.

## Recorrido y evidencia

1. En Home, cargar los datos, verificar la diferencia entre cargados/verificados,
   comprobar versión/perfil y lanzar. Lanzar no debe abrir Actualización.
2. En la intro, observar al protagonista caminando: cámara estable en reposo,
   sin vibración del modelo. Probar ratón y mando por separado, pérdida de foco,
   recaptura y reconexión; registrar qué dispositivo produce cualquier movimiento.
3. Apuntar a Pikachu quieto y en movimiento, con zoom y sin zoom. Conservar
   capturas de la retícula/nombre y anotar si los fragmentos siguen al sujeto.
4. Tomar fotos válidas de Pikachu y Vivillon, revisar imagen y miniatura, completar
   selección/evaluación y entrar en la primera expedición por el flujo original.
   No editar progreso, sujetos ni puntuaciones para poder continuar.
5. Cerrar normalmente y volver a abrir el álbum. En una copia del perfil, ejecutar
   `tools/audit_saved_photos.py --help` y seguir sus opciones de auditoría. Adjuntar
   el informe y, de forma privada, los bancos afectados si persisten franjas.
   Una captura de pantalla por sí sola no localiza si el daño está en el JPEG.
6. Comparar el color con la salida original de Snap sin filtros del port. Registrar
   si continúa la diferencia percibida; la comparación digital local no valida
   el monitor ni la cadena física AMD.
7. Medir el mismo recorrido con caché caliente y sin compilaciones o capturas
   diagnósticas concurrentes. Conservar frametimes completos: p50/p95/p99/máximo,
   además del promedio. No inferir FreeSync activo únicamente por FIFO/mailbox.

Los cambios de sensores físicos se realizan de forma explícita. Una prueba de
un mando no acredita todos los modelos; registrar modelo, conexión y mapeo Switch.
FSR 3.1/4 y DLSS se validan según disponibilidad real de esa GPU, sin presentar
un modo no soportado como activado.

## Si vuelve a ocurrir el bloqueo del tutorial

Conservar el registro, bancos y capturas en la copia de prueba antes de intentar
recuperación. La hipótesis comunicada por el propietario es que mouse/giroscopio
desplazaba la cámara; no está autorizado cambiar la lógica de selección para
aceptar fotos sin sujeto. Reiniciar una ruta sobre una copia de un respaldo
anterior aporta una reproducción limpia; no prueba que el guardado bloqueado se
haya recuperado. No sobrescribir la partida original para forzar ese resultado.

## Resultado

Cada caso conserva dispositivo, binario, recorrido y resultado: aprobado,
fallido o no ejecutado. Los casos no ejecutados permanecen pendientes. Informes
de auditoría, fotos, perfiles y ejecutables derivados quedan privados en `build/`.
