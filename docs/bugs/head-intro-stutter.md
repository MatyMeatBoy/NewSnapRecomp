# HEAD-INTRO · La cabeza del personaje vibra al entrar caminando en la intro

Estado: **REVISIÓN** · Responsable: MatyMeatBoy · 2026-11-14
Equipo: RTX 4060 Laptop, runtime de la línea 0.5 (`e314751d` reconstruido).
**Causa no identificada; sin corrección.** Este informe acota el problema con
medidas y descarta las causas de ritmo.

Nota de procedencia: el reporte original se hizo en la RX 6900 XT con un
runtime de la generación 0.1.x (ver `keyboard-after-photo.md`). Lo medido aquí
es el comportamiento del runtime actual en RTX.

## Resultado

| Afirmación | Clase | Evidencia |
|---|---|---|
| El efecto existe en el runtime actual y no depende de la GPU del reporte | **Observado** | Medido en RTX 4060: la cabeza avanza a pasos desiguales mientras el fondo avanza uniforme |
| No son fotogramas tardíos | **Observado** | Intervalos de presentación 16,67 ms de media, desviación 1,0–1,7 ms, máximo 21,9 ms en la toma |
| No es la cámara | **Observado** | Irregularidad del fondo 0,004 (cuatro ejecuciones), 60 veces menor que la de la cabeza |
| No lo causa la variación del tiempo que mide el juego | **Comprobado por experimento** | Con pasos de tiempo exactos (desviación 0,02 ms) la medida es idéntica: 0,248 frente a 0,248 |
| No depende de cargas, CRC ni trabajo en segundo plano | **Observado** | La secuencia de movimiento se repite igual en cuatro ejecuciones (0,2482 / 0,2479 / 0,2456 / 0,2482) |
| No es solo un artefacto de presentar a 60 lo que se anima a 30 | **Observado** | A 30 fps la irregularidad de la cabeza sigue siendo 0,20 |
| El movimiento desigual es real, no ruido de la medida | **Observado** | Dos mitades de la cabeza medidas por separado muestran la misma alternancia; el ruido del método en el fondo es de 0,004 px |
| Qué subsistema del juego lo produce | **Sin determinar** | Ver hipótesis |
| Si la consola original lo muestra igual | **Sin determinar** | No hay captura de referencia de hardware real |

## Qué se midió

Toma: el personaje entra de espaldas hacia el laboratorio, justo antes del
logo (presentaciones ≈2775–2858 a 60 fps en un perfil nuevo con la ruta
`tests/routes/initial-setup.txt`).

Método (`tools/measure_region_motion.py`): el registrador de vuelo del runtime
(`AC_FLIGHT=1`) guarda una miniatura por presentación en memoria, sin frenar el
juego. Sobre fotogramas consecutivos se mide el desplazamiento subpíxel de tres
rectángulos — cabeza, torso y fondo (el laboratorio, que solo refleja la
cámara) — y su regularidad:

- **irregularidad**: desviación de cada paso respecto a su media móvil de 5
  fotogramas, relativa al tamaño del paso;
- **alternancia**: la parte de esa desviación que cambia de signo cada
  fotograma (lo que haría un componente actualizado a mitad de cadencia).

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
| `head01-fps30` (tope 30, ruta a 30) | 30 | 33,3 ± 1,3 | 0,202 | 0,170 | 0,003 |

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
0,02 ms. Efecto sobre el movimiento de la toma: **ninguno** (tabla). La toma
tampoco cambia entre ejecuciones con variaciones de ritmo distintas. Conclusión:
la escena avanza de forma determinista por fotograma, y ni el temporizador
medido ni el ritmo de presentación producen el tirón.

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
   inestabilidad amplificaría una diferencia pequeña. No hay evidencia; es la
   única hipótesis que haría de esto un defecto del port.
3. **Datos de animación** con claves a otra cadencia muestreadas sin
   interpolar. Menos probable: la irregularidad persiste a 30 fps.

## Qué falta para cerrar

- Una referencia de hardware real de la misma toma (vídeo a 60 Hz de la
  consola): decide entre comportamiento original y defecto del port.
- Si es defecto: localizar el subsistema comparando la toma con las
  estimaciones NEON forzadas a aritmética exacta, o trazando la matriz del
  hueso de la cabeza.
- No modificar la simulación 30/60 ni el temporizador para «suavizar»: el
  experimento muestra que no es ahí.

## Herramienta y pruebas

`tools/measure_region_motion.py` (solo lectura) + `tests/test_region_motion.py`
(7): recuperación de traslaciones subpíxel, contenido cambiado detectado por el
residuo, series uniforme/alternante/aleatoria/acelerada, sujeto desigual sobre
fondo uniforme en fotogramas sintéticos, huecos nunca puenteados, CLI que no
escribe en la carpeta de fotogramas.

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
