# PR #2: correcciones del contrato de applets

Revisión para integración 0.6 desde `732671b`. No valida AMD ni modifica la
continuación JPEG, corregida separadamente desde 0.3. Tampoco identifica el
origen del teclado de Windows. No se tocaron progreso, fotos o guardados.

## Procedencia y booleano de red

Inspección local de los inputs privados Snap 2.0.1, sin copiarlos a Git:

- Main build ID `ddb900ff04a912ed42430508389853cfaf1accce`.
- SDK build ID `0617f669301f922a811886048dd7b41a249cc1b3`, SHA-256
  `86cbb6d9f9e2d83dca0fed1f2081ff3adb88ad5b663b6d05b551927769505574`.

`nn::nifm::HandleNetworkRequestErrorResult` en SDK `+0x32e950` normaliza
el retorno a bit 0 en ambas salidas: es **bool**, no `Result`. El miembro en
`+0x330170` devuelve false en fallos intermedios; al terminar solo devuelve true
si su resultado interno es cero o `0x17c6e`. La política host sin conexión
devuelve ahora `false` exacto, sin solicitar reintento.

Los tres callers main `+0x537a00`, `+0x537a2c`, `+0x53b7ec` usan PLT
`+0xa383a0`, GOT `+0xcc7278`, y prueban bit 0 en la instrucción siguiente.
El valor anterior 622 tenía ese bit a cero, por lo que coincidía accidentalmente
con la rama false de estos callers; no se ha demostrado que cambiara esa rama
en este dump. Sin embargo, era un booleano inválido y una prueba por valor no
cero produciría una respuesta contradictoria. El fixture exige cero exacto y
coincidencia entre ambos gates; falla contra el C original y pasa al corregirlo.

## Cuenta: no sustituir descripciones desconocidas

Los wrappers SDK `+0x15550`, `+0x15580`, `+0x15650` delegan en servicios o
clientes de cuenta. Su código no proporciona por sí solo el resultado exacto
de una consola sin cuenta enlazada. No se inventa una descripción alternativa.

Los callers **sí distinguen descripciones**, además de módulo/éxito:

- Main `+0x538cac..0x538cc4` y `+0x538d50..0x538d68` clasifican módulo 124,
  descripciones 200–269, como estado 3.
- `+0x538e34..0x538e5c` distingue también 430–499.
- `+0x1f2b10..0x1f2b28` usa 430–499 para una ruta con reintentos acotados.

El anterior 124/100 quedaba fuera de esos rangos y llegaba al manejador común
`+0x5443d0`; no se acreditó que esa ruta fuera una cancelación segura equivalente.
Se retiraron únicamente los cuatro overrides especulativos de ensure/id/token.
El SDK original sigue atendiendo esas llamadas, **sin soporte host garantizado**:
pueden fallar por servicios no implementados o cliente no inicializado.

Se conserva `IsNetworkServiceAccountAvailable`: consulta exitosa del estado local
con un único byte false; no crea cuenta, ID, token ni contexto asíncrono. El
fixture verifica el byte adyacente intacto y la lista exacta de 13 registros,
impidiendo reintroducir inadvertidamente los cuatro overrides retirados.

## Otros límites revisados

`ApplicationErrorArg` usa número u32 en +8 y textos en +0x14/+0x814, verificados
en constructores SDK `+0x15c650/+0x15c670`. Las copias para el log están acotadas.
`ErrorResultVariant` verifica tag de 4 bytes y payload máximo de 8 en +4
(constructores `+0x15ca00/+0x15ca20`): el log lee solo esos 12 bytes. Un fixture
con exactamente 12 bytes legibles falla antes de esa corrección y pasa después.

Los fallos sintéticos `nifm` 110/1 y `album` 206/1 son política explícita del
host; sus descripciones de consola no están derivadas. Los callers revisados
de dirección IP `main+0x179df0`, proxy `+0x2475c0` y guardar captura
`+0x7d5844` toman ramas de fallo con resultados no cero. El fixture conserva
salidas sin inventar conexión, proxy o captura guardada. Esto no sustituye una
prueba integrada de esas rutas ni garantiza un mensaje idéntico al de consola.

## Validación y aceptación pendiente

`python -m unittest tests.test_snap_applets -v`: cuatro tests focalizados,
fixture C compilado con `-Wall -Wextra -Werror`. El overlay también pasa
`clang -fsyntax-only -Wall -Wextra -Werror` con el `host.h` real del donor.
El escaneo de duplicados se ejecutó adicionalmente contra el donor y los
overlays del checkout de integración, ya que el worktree aislado no contiene
el submódulo inicializado.

No se ejecutó GPU ni suite completa. Las pruebas RTX anteriores pertenecen al
PR original de 17 registros y no validan este C revisado; falta build integrado
y aceptación de las rutas nuevas. El reporte AMD del usuario sigue abierto.
