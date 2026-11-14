# HEAD-INTRO · La cabeza del personaje vibra al entrar caminando en la intro

Estado: **REVISIÓN** · Responsable: Claude · 2026-11-14
Equipo: RTX 4060 Laptop, runtime privado de diagnóstico derivado de `e314751d`.
SHA256 medido: `6221080431d8c18ac1de5b30ebb1df6629e6408dee0ad33dfa8253100c53c08c`.
**Causa no identificada; sin corrección.** Este informe acota el problema con
medidas de una toma y una intervención sobre su temporizador. No descarta en
general causas de pacing, carga, driver ni diferencias de otros subsistemas.

Nota de procedencia: el reporte original se hizo en la RX 6900 XT con un
runtime de la generación 0.1.x (ver `keyboard-after-photo.md`). Lo medido aquí
es el comportamiento de ese binario de diagnóstico en RTX, no una validación
del ejecutable público ni de la cadena física AMD.

## Resultado

| Afirmación | Clase | Evidencia |
|---|---|---|
| En esta toma RTX se mide desplazamiento desigual de la región de la cabeza | **Observado** | Índice ≈0,25 en cabeza, ≈0,11 en torso y ≈0,004 en fondo; no establece independencia de GPU |
| La cadencia registrada tiene media cercana a 60 FPS en la ventana medida | **Observado** | Intervalos del registrador: media ≈16,67 ms, desviación 1,0–1,7 ms, máximo 21,9 ms; no son timestamps de presentación física |
| El fondo medido es más uniforme que la cabeza en estas regiones | **Observado** | Índice ≈0,004 en cuatro ejecuciones; no excluye toda contribución de cámara ni calibra el ruido del método |
| Cuantizar el temporizador no eliminó la irregularidad medida en esta toma | **Intervención acotada** | Desviación del paso baja a 0,02 ms; índice de cabeza 0,248/0,246 frente a 0,248/0,248 sin cuantizar |
| Las cuatro ejecuciones tienen índices similares | **Observado** | 0,2482 / 0,2479 / 0,2456 / 0,2482; esto no demuestra igualdad de todas las trayectorias ni descarta cargas, CRC o trabajo de fondo |
| Comparación cuantitativa equivalente a 30 FPS | **Pendiente** | Existe una corrida exploratoria; falta el JSON de esta herramienta con ventana, regiones y conteos auditables |
| Las dos mitades de la cabeza presentan patrones parecidos | **Observación exploratoria** | No es una calibración independiente del error óptico ni prueba por sí sola una causa de animación |
| Qué subsistema del juego lo produce | **Sin determinar** | Ver hipótesis |
| Si la consola original lo muestra igual | **Sin determinar** | No hay captura de referencia de hardware real |

## Qué se midió

Toma: el personaje entra de espaldas hacia el laboratorio, justo antes del
logo (presentaciones ≈2775–2858 a 60 fps en un perfil nuevo con la ruta
`tests/routes/initial-setup.txt`).

Método (`tools/measure_region_motion.py`): el registrador de vuelo del runtime
(`AC_FLIGHT=1`) guarda miniaturas por presentación en memoria. Su coste diagnóstico
no es cero. Sobre fotogramas consecutivos se mide el desplazamiento subpíxel de tres
rectángulos — cabeza, torso y fondo (el laboratorio, que solo refleja la
cámara) — y su regularidad:

- **irregularidad**: desviación de cada paso respecto a su media móvil de 5
  fotogramas, relativa al tamaño del paso;
- **alternancia**: la parte de esa desviación que cambia de signo cada
  fotograma (lo que haría un componente actualizado a mitad de cadencia).

Ambos índices son adimensionales. Se conservan los índices originales de frame:
los huecos y pares rechazados separan segmentos, sin inventar adyacencia ni
reiniciar la fase par/impar. `frames` cuenta pares aceptados, `discarded` los
rechazados por residuo, `segments` las secuencias contiguas y `analyzed_pairs`
los pares interiores que participan en la métrica tras recortar los bordes.
Los segmentos demasiado cortos no dan un veredicto.

Las capturas a tamaño completo (`AC_SHOTS_FULL`) no sirven para esto: escribir
8 MB por fotograma frena el juego y altera el movimiento. Las miniaturas se
tomaron a 640×360 desde una ventana de 1280×720 con un runtime privado de
diagnóstico (el tamaño de miniatura es una constante de compilación; a 320×180
la gorra tiene poca textura y a 960×540 se pierden fotogramas).

| Ejecución (`build/…`) | Cadencia | Paso de tiempo del juego (ms, desv.) | Cabeza | Torso | Fondo |
|---|---|---|---|---|---|
| `head01-ab-off-1` | 60 | 16,69 ± 1,03 | 0,248 | 0,109 | 0,004 |
| `head01-ab-on-1` (tiempo exacto) | 60 | 16,68 ± 0,02 | 0,248 | 0,109 | 0,003 |
| `head01-ab-on-2` (tiempo exacto) | 60 | 16,68 ± 0,02 | 0,246 | 0,091 | 0,004 |
| `head01-ab-off-2` | 60 | 16,66 ± 1,71 | 0,248 | 0,109 | 0,004 |
| `head01-fps30` (exploratoria) | 30 | Comparación pendiente | — | — | — |

Cada JSON `motion.json` de las cuatro corridas a 60 FPS conserva la ventana
2775–2858, 83 pares por región y cero descartes. Los conteos y regiones forman
parte de la comparación; no deben mezclarse índices de métodos o ventanas
distintos. La corrida a 30 FPS conserva `flow.json` de un análisis exploratorio
anterior, pero no un `motion.json` equivalente. Los antiguos valores 0,202/0,170/
0,003 quedan fuera de esta tabla hasta regenerar y conservar ese informe con
ventana y regiones explícitas; no permiten descartar una causa por cadencia.

Ejemplo de pasos horizontales consecutivos de la cabeza a 60 fps (px a
640×360): 2,00 · 1,29 · 1,81 · 1,19 · 1,56 · 1,18 · 1,38 · 1,23, con el fondo
en 1,07 · 1,09 · 1,10 · 1,11 · 1,13 · 1,14 · 1,15 · 1,16 en los mismos
fotogramas. La alternancia alto/bajo aparece en ráfagas (≈2773–2784, 2789–2800,
2821–2832), no en toda la toma, por eso el índice global de alternancia es bajo
(0,012) y el de irregularidad alto.

## Experimento: tiempo de fotograma exacto

El temporizador de fotograma del juego (`main+0x6abea0`) mide el tiempo real
entre actualizaciones; sus tres canales están siempre en modo «medido» (traza de
3 586 llamadas, un solo sitio de llamada). En el host ese tiempo oscila entre
≈12 y ≈22 ms aunque la media sea exacta.

En un runtime privado se dio a esa actualización un instante anterior tal que
el paso medido fuera un número entero de periodos de 60 Hz, con un reloj ideal
que sigue al real sin deriva. Efecto sobre el paso: desviación de 1,0–1,7 ms a
0,02 ms. No se observa que elimine la irregularidad de la región medida (tabla). La toma
tiene índices parecidos entre ejecuciones con variaciones de ritmo distintas,
aunque no idénticas en todas las regiones. Conclusión acotada: esta intervención
redujo la variación del temporizador sin eliminar la irregularidad óptica de
la región medida. No demuestra que el ritmo de presentación, el driver o todos
los temporizadores y subsistemas del juego sean ajenos al síntoma.

El experimento escribe en un campo del temporizador del juego; es solo un
instrumento de diagnóstico, no una corrección propuesta, y no está en este PR.
Queda como parche local en `build/head01-diagnostic.patch` (conjunto de parches
`snap_timer_trace`, apagado por defecto, y miniaturas mayores).

## Hipótesis que quedan (ninguna comprobada)

1. **Animación secundaria de la cabeza** (hueso con muelle, gorra o seguimiento
   de mirada) que responde a cada pisada con una oscilación rápida. Encaja con
   las ráfagas separadas ≈40 fotogramas y con que el torso tenga menos. Sería
   comportamiento del juego; faltaría saber si la consola lo muestra igual.
2. **Diferencia numérica de la recompilación** en ese cálculo (estimaciones de
   raíz/recíproco NEON, contracción FMA): un muelle rígido cerca de la
   inestabilidad amplificaría una diferencia pequeña. No hay evidencia que la
   confirme ni que excluya otros posibles defectos del port.
3. **Datos de animación** con claves a otra cadencia muestreadas sin
   interpolar. La comparación equivalente a 30 FPS sigue pendiente; no se usa
   la corrida exploratoria para asignar menor probabilidad a esta hipótesis.

## Qué falta para cerrar

- Una referencia de hardware real de la misma toma (vídeo a 60 Hz de la
  consola): decide entre comportamiento original y defecto del port.
- Si es defecto: localizar el subsistema comparando la toma con las
  estimaciones NEON forzadas a aritmética exacta, o trazando la matriz del
  hueso de la cabeza.
- Mantener la simulación 30/60 y la lógica originales. La intervención actual
  no justifica proponer una modificación del temporizador como corrección.

## Herramienta y pruebas

`tools/measure_region_motion.py` (solo lectura) + `tests/test_region_motion.py`
(10): recuperación de traslaciones subpíxel, contenido cambiado detectado por el
residuo, series uniforme/alternante/aleatoria/acelerada, sujeto desigual sobre
fondo uniforme en fotogramas sintéticos, huecos nunca puenteados, CLI que no
escribe en la carpeta de fotogramas. Las regresiones de revisión preservan
paridad y segmentos al rechazar un paso de una serie alternante de 40, y no
calculan métricas juntando segmentos individualmente insuficientes. El defecto
anterior reducía falsamente la alternancia de 0,24 a 0,0072 al rechazar un paso;
corregido da ≈0,238, con la pequeña diferencia debida al nuevo promedio de paso.
Las cuatro mediciones a 60 FPS no descartaban pares: no quedan invalidadas por
este defecto, pero sus conclusiones mantienen los límites anteriores.

```
python tools\measure_region_motion.py <volcado AC_FLIGHT> --first 2775 --last 2858 --box cabeza:284,116,384,208 --box torso:276,232,380,320 --box fondo:40,80,200,220
```

## Límites

- Una sola toma, una sola GPU (RTX 4060) y una sola resolución de medida.
- La irregularidad incluye la aceleración natural del caminar; por eso se
  compara siempre con el torso y el fondo de la misma toma, no con cero.
- Los rectángulos son fijos; se descartan pares cuyo residuo indica cambio de
  contenido.
- No se ha medido en la RX 6900 XT con un runtime actual.
