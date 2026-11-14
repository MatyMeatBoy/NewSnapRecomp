# NaN en shaders traducidos en AMD: guía para recomps de Switch

2026-11-14 · Claude. Caso real: CRISTAL-01 (Cristalflor negra en RX 6900 XT). Esta guía sirve
para cualquier port que traduzca shaders de Maxwell a SPIR-V (traductor de Ryujinx, yuzu y
derivados) y vea objetos negros, halos o manchas solo en AMD.

## Síntoma

- Un objeto, o una parte de él, sale **negro sólido** en AMD y bien en NVIDIA.
- Con antialiasing temporal (FSR, DLAA, TAA) aparece además un **halo** o "ghosting" negro
  alrededor, porque el historial arrastra el NaN a los fotogramas siguientes.
- En casos graves, un NaN que llega a un pase de desenfoque o de reducción se extiende por toda
  la pantalla.

## Causa

La GPU de la Switch (Maxwell) y Vulkan no tratan igual los valores especiales:

| Operación | Maxwell (Switch) | SPIR-V que emite el traductor | AMD | NVIDIA |
|---|---|---|---|---|
| `min/max` con un NaN | devuelve el otro operando (FMNMX) | `FMin/FMax`: **indefinido** | puede devolver NaN | devuelve el otro |
| `saturate(NaN)` | 0 (`.SAT`) | `FClamp(x,0,1)`: **indefinido** | puede dar NaN | 0 |
| `sqrt`/`log2` de un casi-cero | el cálculo da ≥ 0 | `Sqrt/Log2` | a veces da −ε, y sqrt/log2 de −ε es NaN | suele dar 0 |

El último caso viene de la precisión: un `fma(dot(n, l), 0.5, 0.5)` con vectores normalizados
puede salir ligeramente negativo en AMD y exactamente 0 en NVIDIA.

## Cómo diagnosticarlo (sin adivinar)

1. Volcado del fotograma con el defecto en pantalla (`AC_DUMP_KEY=1`, F12).
2. En `images.txt`, buscar el **primer pase con `nan N`** mayor que 0. El pase anterior limpio y
   el siguiente con NaN acotan el dibujo culpable.
3. En `passes.txt`, ese pase da los ids de los shaders (`vs`/`fs`). Los binarios están como
   `sh_<id>.spv` en algún volcado de la sesión.
4. Decompilar con `spirv-cross --vulkan-semantics` y contar
   `FClamp/FMin/FMax/Sqrt/InverseSqrt/Log2` (`spirv-dis`).
5. `AC_DUMP_UBO=48` añade los buffers de constantes, por si el NaN viene de datos y no de
   la matemática.

## Arreglo aplicado en NewSnap (`newsnap/spirv_nminmax_adapt.py`)

Se reescribe cada módulo justo antes de `vkCreateShaderModule` (`make_module` en
`vk_pipeline.c`). No toca el traductor ni su caché:

- `AC_SPIRV_NMINMAX`: GLSL.std.450 `FMin`(37)/`FMax`(40)/`FClamp`(43) pasan a
  `NMin`(79)/`NMax`(80)/`NClamp`(81). Es la semántica exacta de Maxwell.
- `AC_SPIRV_DOMAIN_CLAMP`: antes de `Sqrt`(31)/`InverseSqrt`(32)/`Log2`(30) se inserta
  `NMax(x, 0)`, con una constante nula por tipo.
- Ambos activos por defecto en AMD y apagados en el resto, para que NVIDIA siga dando
  exactamente lo mismo. Coste: el primer arranque recompila los pipelines en el driver.
- Validación: `spirv-val --target-env vulkan1.3` sobre los 89 shaders distintos de los
  volcados del propietario, sin ningún error. En el juego: 0 pases con NaN y el cristal correcto.

## Errores a evitar

- No "arreglar" el NaN al final del shader ni en el pase de salida: esconde la causa y deja
  mal la iluminación.
- No ordenar −0 por debajo de +0 en `NMin/NMax`: ocarina-recomp lo probó y la imagen salió
  blanca entera.
- No cambiar la matemática en NVIDIA sin necesidad: allí el resultado ya coincide con la Switch.
- Una sola sesión buena no atribuye la causa. Para saber cuál de los dos ajustes la arregla,
  apagar uno cada vez (`AC_SPIRV_NMINMAX=0` / `AC_SPIRV_DOMAIN_CLAMP=0`).

## Fuentes (casos equivalentes en otros proyectos)

- Lichii, issue #325 (AMD, Ocarina of Time: neblina y agua brillante por NaN en FMin/FMax/FClamp):
  <https://github.com/zortos293/Lichii/issues/325>
- Lichii, PR #432 (min/max/clamp con NaN definido):
  <https://github.com/zortos293/Lichii/pull/432>
- Savage Wind Recomp, PR #153 (NMin/NMax/NClamp; medido en AMD con RADV; no integrado por coste
  de caché y ganancia no medible en NVIDIA): <https://github.com/Revivedx/SavageWindRecomp/pull/153>
- ocarina-recomp, issue #49 (RX 9070 XT: siluetas negras arregladas con `Sqrt(NMax(x, 0))`;
  orden −0/+0 revertido): <https://github.com/sostenesfreitas/ocarina-recomp/issues/49>
- Reglas de coma flotante de Direct3D (min/max devuelven el operando que no es NaN):
  <https://learn.microsoft.com/windows/uwp/graphics-concepts/floating-point-rules>
