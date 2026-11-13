# FOTO-02 · Auditoría CPU de fotos guardadas (bandas negras)

Estado: **REVISIÓN** · Responsable: Claude · 2026-11-13
Equipo de la auditoría: RTX 4060 Laptop (el mismo de Codex). **No hay bytes
generados en la RX 6900 XT del propietario en este equipo**; ver Límites.

## Pregunta

¿Las bandas negras de fotos y miniaturas están en los bytes guardados
(captura → readback → JPEG) o solo en la vista previa (textura/presentación)?

## Resumen

| Afirmación | Clase | Evidencia |
|---|---|---|
| Las fotos y miniaturas guardadas localmente (NVIDIA) están limpias en bytes | **Observado** | 150 bancos en 14 copias de perfil, 0 bandas, 0 bloques negros, CRC/Adler/estructura JPEG correctos |
| El fallo del propietario (AMD) aparece en la pantalla de selección **antes de guardar** | **Observado** | Captura `b8af3c5e`: vista previa y las 2 miniaturas de la tira con franjas; mensaje «No puedes seleccionar una foto sin un sujeto que se vea claramente» |
| Las franjas AMD no son bandas de ancho completo: son tramos válidos contiguos en orden de franjas de 48 filas | **Observado** (medido en la captura) | Geometría abajo |
| Las fotos AMD con franjas probablemente nunca llegaron al banco 3/4 | **Inferido** | El juego no dejó seleccionarlas; no existe ningún guardado posterior a las 16:53 en este equipo |
| El defecto está aguas arriba del JPEG (textura/readback sin comprimir) | **Hipótesis sin comprobar** | Vista previa y miniaturas muestran la misma corrupción y coincide el rechazo del sujeto. La coincidencia no demuestra que la evaluación lea esos píxeles ni excluye presentación, pitch o JPEG |
| Si el JPEG AMD guardado contiene las franjas | **Sin determinar** | Requiere ejecutar la herramienta sobre una copia de un guardado AMD |

## Herramienta

`tools/audit_saved_photos.py` (solo lectura, CPU):

- Abre los bancos 3 (`00c31e53dde3ac51`, fotos) y 4 (`4f342de95be7450e`,
  miniaturas) con `shared_read`; calcula SHA-256 del archivo antes y después
  (`unchanged_after_read`).
- Por posición: magia, longitudes, Adler-32 y CRC-32 por separado, metadatos,
  relleno tras EOI. A diferencia de `saves.saved_jpegs`, no se detiene en la
  primera entrada dañada.
- Por JPEG: recorrido de segmentos (SOF, muestreo, DRI, secuencia RST, EOI),
  decodificación completa con Pillow, dimensiones SOF vs. decodificadas.
- Píxeles: filas/columnas negras (≥98 % con canal máx. ≤24) clasificadas
  `edge`/`interior` y alineación a 8/16; proporción de bloques 16×16 totalmente
  negros (`black_block_fraction`, sospechoso ≥1 %) para franjas de ancho parcial.
- Veredicto: `bandas-en-bytes-de-foto`, `bandas-solo-en-miniaturas-guardadas`,
  `incompleto-o-dañado`, `bytes-limpios` o `sin-fotos`. `bytes-limpios` exige
  evidencia completa: todos los bancos leídos, tamaños coherentes, checksums
  válidos, todos los JPEG decodificados y sin problemas de estructura. Cualquier
  excepción queda en `summary.incidencias`. Código de salida: 0 limpio, 1 con
  bandas, 2 incompleto.
- Un JPEG malformado o un error por entrada no detiene el resto del banco.
- Salidas: nunca coinciden con un banco de entrada (misma ruta, enlace
  simbólico o hardlink), ni caen en la carpeta de un banco de entrada, ni usan
  un nombre de archivo de guardado, ni entran en `save`, `save-tx`,
  `save-backup`, `GameData` o `newsnapGameData`. Se comprueba antes de leer y
  otra vez al escribir cada archivo. El informe JSON no contiene imágenes;
  `--export-flagged` copia solo los JPEG marcados a una carpeta local.

```
.venv\Scripts\python -X utf8 tools\audit_saved_photos.py <copia-de-perfil> --out build\photo-audit\informe.json --export-flagged build\photo-audit\flagged
```

## Resultados locales (NVIDIA)

Comando: todos los perfiles con `save/` bajo `build/` más sus `save-tx/work`
→ `build/photo-audit/all-build-copies.json` (1 min 34 s).

- 150 bancos leídos, 0 errores de cabecera, 0 tamaños incoherentes, 0 archivos
  modificados por la lectura.
- 136 bancos solo con posiciones vacías (954 posiciones de foto, 252 de miniatura).
- 14 perfiles (`v03-final-native-smoke` … `v05-original-pacing-warm-02`)
  comparten las mismas 2 fotos de la ruta del tutorial de la 0.3:

| Banco | Pos. | SHA-256 (16) | Tamaño | JPEG | Bytes | Bandas | Bloques negros |
|---|---|---|---|---|---|---|---|
| fotos | 0 | `8c17e804a8352074` | 1080×720 | baseline 4:2:0, sin DRI | 379 697 | ninguna | 0 % |
| fotos | 1 | `62553a0656964a2c` | 1080×720 | baseline 4:2:0, sin DRI | 434 350 | ninguna | 0 % |
| miniaturas | 0 | `5cf214065a29b1ea` | 240×200 | baseline 4:2:0, sin DRI | 39 984 | ninguna | 0 % |
| miniaturas | 1 | `505f067149be2290` | 240×200 | baseline 4:2:0, sin DRI | 38 395 | ninguna | 0 % |

Inspección visual de la foto 1 y su miniatura: imagen completa y coherente.
`newsnapGameData/profile` (solo lectura, sin tocar) tiene los bancos vacíos y
sin cambios desde las 04:26; las fotos del informe del propietario (16:53:29) no
están en este equipo.

## Geometría de las franjas en la captura AMD

Captura `build/user-reports/codex-clipboard-b8af3c5e-….png` (1600×901; la vista
previa ocupa 601×401 px ≈ 1080×720 × 0,556):

- Transiciones verticales cada ≈26,7 px de pantalla = **48 filas de foto**
  (15 franjas). No hay cortes a media franja.
- Dentro de una franja el corte horizontal cae en x ≈ 215, 285, 503, 573, 791,
  861 px de foto (no es una rejilla de teselas en X).
- Recorriendo la imagen como 15 franjas de 1080×48 concatenadas, los tramos
  **válidos** son ≈[70, 1080), [4102, 5112), [8134, 9144), [12166, 13176): unos
  **1010 px de franja válidos cada 4032**, es decir, ≈1 de cada 4 tramos
  contiguos; el resto es negro puro (canal máx. ≤6).
- Mapa de 15×15 (`.` válido, `#` negro, `?` mixto/tapado por la UI):

```
.........?.....
??############?
###############
############...
...........####
###############
###############
########.......
.......########
###############
?##############
?###...........
...############
#??############
###??##########
```

Lectura (hipótesis para orientar pruebas de FOTO-01, **no una causa
determinada**): el contenido válido parece estar en su sitio y el resto en
negro, con periodicidad en un orden por franjas de 48 filas. Una explicación
compatible es una copia/subida/readback troceado en el que solo llega parte de
los trozos (rangos de buffer, páginas sucias, trabajos paralelos incompletos).
La medición procede de una captura reescalada y no excluye por sí sola errores
de pitch, de presentación o del JPEG. Prueba sugerida: buscar en el renderer
qué recorre la imagen de 1080×720 en franjas de 48 filas o en trozos de
≈1008×48 px (≈193 536 bytes en RGBA8) y volcar la textura de captura.

## Relación con otras tareas

- **FOTO-01**: punto sugerido para instrumentar primero: la textura de captura
  sin comprimir y su readback en AMD, antes del codificador JPEG.
- **TUTO-01**: el mensaje «sin un sujeto que se vea claramente» aparece con las
  mismas fotos corruptas. Es solo una coincidencia observada; no hay prueba de
  que la evaluación lea esos píxeles.
- La comparación foto↔miniatura del informe es solo orientativa: las miniaturas
  son recortes 6:5 con desplazamiento horizontal distinto por foto (120 y 192 px
  en las dos muestras), no una reducción de la foto.

## Pruebas

```
.venv\Scripts\python -X utf8 -m unittest tests.test_photo_audit tests.test_photos
```

25 pruebas OK (20 en `tests/test_photo_audit.py`: bandas interiores/de
borde/columna tras JPEG, franja de ancho parcial, todo negro, estructura y
truncado, banco limpio sin modificar, bandas en foto, bandas solo en miniatura,
entrada con checksum inválido sin ocultar el resto, clave errónea, negativa a
escribir dentro del guardado, y las regresiones de la revisión).

## Respuesta a la revisión de Codex (`photo-audit-review.md`)

1. **Salida sobre entrada (P1)** — corregido: `check_output`/`safe_write`
   comparan cada salida con todos los bancos descubiertos. Regresiones:
   `--out` igual al banco, en su carpeta, hardlink al banco, nombre de banco en
   otra carpeta, exportación dentro de la carpeta de entrada.
2. **JPEG malformado aborta (P2)** — corregido: longitudes mínimas de SOF/DRI,
   analizador protegido y errores conservados por entrada. Regresiones con SOF
   C0 y DRI de longitud 2, solos y dentro de un banco con otra foto válida.
3. **Veredicto limpio con JPEG ilegible (P1)** — corregido: veredicto
   `incompleto-o-dañado` y salida 2. Regresión con el JPEG exacto de la revisión.
4. **Fuerza de las inferencias** — rebajadas a hipótesis en este informe.

Tras las correcciones se repitió la auditoría sobre tres perfiles
representativos (`v03-jump-fixed`, `v05-original-color-chain`,
`v04-production-neutral-fsr31`): `bytes-limpios`, evidencia completa.

## Límites

- Ningún byte generado en AMD ha sido auditado. El veredicto «bytes limpios»
  vale solo para NVIDIA RTX 4060 y para 2 fotos de una única ruta.
- La geometría AMD se mide sobre una captura de pantalla reescalada (±2 px de
  foto); los tamaños de trozo son aproximados.
- La detección de bloques negros puede marcar escenas legítimamente muy
  oscuras (cuevas, noche); `--export-flagged` existe para revisarlas a ojo.
- No se modificó `saves.py`, `photos.py` ni ningún punto de integración.

## Siguiente paso propuesto (propietario, AMD)

1. Con el juego cerrado, copiar el perfil a una carpeta de trabajo y ejecutar
   la herramienta sobre la copia. Si el guardado tiene fotos, el veredicto
   decide entre captura (bytes) y vista previa.
2. Si no llegó a guardarse ninguna foto (softlock del tutorial), la prueba
   decisiva es un volcado de la textura de captura desde el renderer (FOTO-01).
