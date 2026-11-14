# Revisión de PR #2: applets y triaje del cierre

Revisión de `732671b35668b4ed0d275e3c6e6da217107e64bb`.
PR: https://github.com/MatyMeatBoy/NewSnapRecomp/pull/2
CI Source checks pasa. No integrar el overlay sin resolver estos contratos.

## Retorno booleano

`nn::nifm::HandleNetworkRequestErrorResult()` retorna bool, no Result.
El SDK fijado, `sdk+0x32e950`, normaliza el retorno con `and w0,w0,#1`.
Los tres callers observados (`main+0x537a04`, `main+0x537a30`,
`main+0x53b7f0`) usan `tbz w0,#0`. El overlay retorna RT_RESULT(110,1),
622: bit cero falso, valor completo no cero. Corregir a `false` (0) y
comprobar el valor canónico y la coherencia de ambas formas de probar bool.
Los callers actuales toman la misma rama falsa con 622; no se demostró una
rama de juego incorrecta en ese dump. El contrato ABI sí está incumplido.

Cuatro pruebas originales pasan porque esperan el módulo de un Result.
Un fixture nativo independiente con la aserción de bool falla en el código
propuesto: evidencia privada `build/pr2-applet-review/bool-contract/`.

## Errores de cuenta

El comentario «el juego solo comprueba éxito» no es correcto. Los callers en
`main+0x538cac..0x538cc4`, `+0x538d50..0x538d68`,
`+0x538e34..0x538e5c` y `+0x1f2b10..0x1f2b28` distinguen el módulo 124
y rangos de descripciones 200–269 y/o 430–499. El error sintético 124/100
queda fuera. Antes de prometer equivalencia con una consola offline hace falta
justificar el contrato elegido y comprobar su rama consumidora. No sustituir
por otra descripción adivinada ni modificar progreso para ocultar fallos.

## Log del propietario

SHA256 BDBB38B767C3295FFB06BE0C3EB611F20444BBE6AE744BDFDF438D5F39D8680B.
El fatal observado es `rt_dispatch sdk+0x273060`; la inferencia de generación
por líneas/parches del log es útil, pero no identifica criptográficamente el
ejecutable ni demuestra qué abrió el teclado del sistema. El paquete que el
propietario descargó fue el ZIP de GitHub; investigar automáticamente el
ejecutable que pudo iniciar tras el 404 del launcher. No volver a pedirle
que determine versiones manualmente ni cerrar fotos/color/AMD sin validación.

El nuevo exportador del launcher incluye hash e identidad para futuras sesiones.
La reproducción y corrección de teclado siguen reservadas a Claude.
