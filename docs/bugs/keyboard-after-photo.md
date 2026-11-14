# KEYBOARD-CRASH · Teclado de Windows y cierre tras registrar a Pikachu

Estado: **REVISIÓN** · Responsable: MatyMeatBoy · 2026-11-13

## Resultado

El log aportado termina con `rt_dispatch sdk+0x273060`, compatible con el
defecto JPEG/longjmp corregido desde 0.3. Sus parches y líneas de arranque
sugieren un runtime anterior, posiblemente 0.1.x; no hay hash de ese ejecutable.
No permite establecer qué abrió el teclado de Windows ni excluir cualquier
otro fallo en otro binario. La ausencia de `swkbd` solo indica que este log no
registra una llamada a esa entrada de texto.

El propietario descargó el ZIP de GitHub y debió iniciar a la fuerza tras el
404. Identificar por separado paquete y ejecutable es necesario. Fotos/color
AMD siguen pendientes de repetición con identidad registrada; este indicio no
autoriza a desestimar sus síntomas ni dar por verificada una versión distinta.

## Evidencia: log de la sesión AMD

Copia privada: `build/user-reports/rx6900xt-0.5/logs/astralchain.log`
(59 271 bytes, SHA-256 `bdbb38b7…d8680b`), entregado por el propietario. No se
sube a Git. Salida de `tools/triage_game_log.py`:

| Dato | Valor en el log | Lectura |
|---|---|---|
| Carpeta de ejecución | La carpeta del port del propietario (ejecutable, `exefs`, `romfs` y `astralchain.ini` en la raíz) | Disposición de la prueba portátil 0.1.x, no `GameData` |
| Conjuntos de parches | `patches: snap_render on` | 0.2–0.4 imprimen además `snap_supersample`; 0.5 añade `snap_random_range` |
| Línea `vk: final SDR byte transfer` | ausente | Existe desde la corrección de color de la 0.5 |
| Escalado | `dlaa: temporal anti-aliasing FSR 3 Native AA`, `FSR scales 1920x1080 to 2560x1440 (sharpness 80)` | Configuración antigua (`astralchain.ini`, 19 claves) activa en esa sesión |
| GPU / driver | AMD Radeon RX 6900 XT, driver propietario 26.10.1 | — |
| Teclado | ninguna línea `swkbd:` | El juego **no** abrió la entrada de texto en esa sesión |
| Final | `FATAL: rt_dispatch: no function at guest pc … (sdk+0x273060): not a function start (lr … sdk+0x273060)` tras el frame 26400 | Fatal del runtime, salida 70 |
| Foco | pierde el foco 22:40:50–22:40:53, lo recupera 22:41:11, fatal inmediatamente después | Coincide con salir del juego y volver; no hay cierre de ventana |

Comprobación de la generación con logs locales: los de 0.1.x
(`build/research/alpha-portable-boot.log`) imprimen `snap_render on` solo; los
de 0.3 y 0.4 (`build/v03-jump-fixed`, `build/v04-production-neutral-fsr31`)
añaden `snap_supersample`; los de 0.5 añaden `snap_random_range`. Es una
inferencia por lo que el runtime imprime al arrancar, no un hash del ejecutable.

## Causa del cierre

`sdk+0x273060` es la instrucción siguiente a una llamada a `setjmp` dentro de la
función del SDK que codifica JPEG (crea el compresor de libjpeg versión 80 con
una estructura de 0x240 bytes y arma `setjmp` para sus errores). Cuando libjpeg
abandona la codificación por `longjmp`, el control vuelve a esa dirección, que
no es inicio de función: un runtime sin continuaciones de salto no puede
seguirla y termina con ese fatal.

- **Mismo fatal reproducido localmente con un runtime antiguo:**
  `build/v03-tutorial-04/run.log` termina con la línea idéntica
  (`sdk+0x273060`), en RTX 4060. No es un síntoma observado exclusivamente en AMD.
- **Corregido desde la 0.3** («live SDK jump continuations»,
  `newsnap/jump_adapt.py`, `overlays/snap_jump.c`): el código generado actual
  arma un punto de retorno nativo en esa misma llamada
  (`snap_jump_arm(…, 0x7002c73060)` en el C generado).
- **Verificado en runtimes actuales:** las ejecuciones de 540 s de RTX tester y la de
  este trabajo (`build/kbd01-applets-photo540`, salida 0) pasan por el registro
  de Pikachu y Vivillon y guardan dos fotos y dos miniaturas.

## El «teclado de Windows»

El log no contiene ninguna llamada a `nn::swkbd::ShowKeyboard`. Una aparición
del teclado táctil al cambiar el foco es una hipótesis; **no está comprobado**
qué lo abrió ni se puede excluir actividad que ese log no registre.

## Por qué se ejecutó un runtime antiguo

No determinado aquí; es trabajo de LAUNCH-404 y AUTO-DATA (RTX tester). Lo que el log
establece: la sesión arrancó desde la carpeta del port del propietario con la disposición
portátil antigua. Si el launcher 0.5 no pudo descargar el kit (404) y se
«inició a la fuerza», se lanzó el ejecutable que ya había allí. Convendría que
el launcher se negara a iniciar un runtime cuya versión no sea la esperada, o
que lo avisara con claridad; `tools/triage_game_log.py` ya lo detecta a
posteriori.

## Auditoría del teclado (hecha antes de recibir el log)

- Un único sitio llama a `nn::swkbd::ShowKeyboard`: `main+0x69ac24`, el apodo
  de la configuración inicial (1–12 unidades UTF-16).
- La ventana real del host, que solo se había usado con respuesta forzada, se
  ejecutó en RTX con `AC_SWKBD_TEST`:

| Ejecución (`build/…`) | Variante | Resultado |
|---|---|---|
| `kbd01-window-ok` | Ventana en segundo plano, OK | salida 0, apodo «Local», llega a la intro |
| `kbd01-window-cancel` | Cancelar | salida 0; el juego repite la petición (27 veces) |
| `kbd01-fullscreen-ok` | Pantalla completa con foco, OK | salida 0; pierde y recupera el foco |
| `kbd01-applets-setup` | Runtime con `snap_applets.c`, OK | salida 0 |

  No cubre mando físico, teclado táctil de Windows ni escritura manual.

## Endurecimiento independiente: applets y contratos de retorno

Este overlay no corrige el cierre JPEG reportado, cuya continuación se trató
separadamente desde 0.3. Las rutas nuevas no se han observado durante una partida
real. La política del host registra diálogos sin UI y mantiene la red y el álbum
de consola sin servicio; no afirma equivalencia exacta con una consola offline.

| Función | Política del host revisada |
|---|---|
| `nn::err::ShowApplicationError` | Registra número y textos acotados; retorna `void` |
| `nn::err::ShowError(ErrorResultVariant)` | Registra solo tag y payload verificados (12 bytes); retorna `void` |
| `nn::nifm::SubmitNetworkRequestAndWait`, `CancelNetworkRequest` | Sin petición real; `void` |
| `nn::nifm::HandleNetworkRequestErrorResult` | **Booleano `false` exacto: sin reintento**, no un `Result` |
| `GetCurrentPrimaryIpAddress`, `GetCurrentProxySetting` | Fallo sintético del host, descripción no derivada de consola |
| `nn::account::IsNetworkServiceAccountAvailable` | Consulta correcta con un byte «no enlazada»; no simula enlazar |
| `nn::friends::Initialize`, `ShowUserDetailInfo` | Sin servicio; acción de perfil cerrada según política host |
| `nn::album::Initialize`, `Finalize`, `SaveScreenshot` | Sin servicio; guardar devuelve fallo sintético, nunca éxito |

Se retiraron los cuatro overrides de cuenta `EnsureNetworkServiceAccountAvailable`,
`GetNetworkServiceAccountId`, `EnsureNetworkServiceAccountIdTokenCacheAsync` y
`LoadNetworkServiceAccountIdTokenCache`: no se pudo derivar el resultado offline o
cancelado exacto. Sus rutas conservan el SDK original y siguen **sin soporte host**;
pueden terminar en servicio no implementado o cliente no inicializado. No se
reemplazan por éxito ni se omiten validaciones de progreso.

La selección de descripción importa: varios callers distinguen rangos de error
de cuenta. Los valores 124/0 y 124/100 del PR original no estaban justificados.
Procedencia, offsets, límites y evidencia RED/GREEN en
[pr2-applet-contracts.md](pr2-applet-contracts.md).

## Herramienta: `tools/triage_game_log.py`

Solo lectura. A partir de un log de sesión (o de la carpeta de logs, eligiendo
el más reciente) informa:

- **Cómo terminó:** `excepción-host` (71), `fatal-runtime` (70),
  `ventana-cerrada` (0), `reinicio-solicitado` (75), `fin-programado`,
  `sin-marca-final`.
- **Qué runtime era:** conjuntos de parches, generación inferida, carpeta de
  ejecución, y aviso si no es de la línea 0.5.
- GPU y driver, último frame, llamadas de teclado, diálogos y servicios, foco,
  bloque fatal con función y frames del juego, y las últimas líneas relevantes.
- Reconoce el fatal del codificador JPEG de los runtimes anteriores a 0.3 y los
  servicios sin implementar, por nombre.

Sustituye rutas de perfil de usuario por `%USERPROFILE%` y no copia datos del
juego.

```
python tools\triage_game_log.py "<carpeta de logs>"
```

Dónde están los logs: con el launcher, `GameData\logs\launcher-game-<sesión>-NNN.log`;
con inicio directo o forzado, `logs\astralchain.log` junto al ejecutable, y las
cuatro sesiones anteriores en `totk.1.log` … `totk.4.log`.

## Pruebas

```
python -X utf8 -m unittest tests.test_snap_applets tests.test_game_log_triage
```

- `tests/test_snap_applets.py` (4): lista exacta de 13 símbolos; ningún otro
  fuente los sustituye; sin escrituras de archivos ni parches; fixture nativo
  con clang `-Wall -Wextra -Werror` que ejecuta cada respuesta y comprueba booleano exacto, gates de caller por bit/valor y lectura limitada a 12 bytes del variant.
- `tests/test_game_log_triage.py` (13): los seis veredictos, servicio con
  nombre, generación del runtime, fatal JPEG conocido, redacción de rutas,
  elección del log más reciente (launcher e inicio directo), solo lectura, logs
  grandes.
- Suite histórica del PR original en el worktree: 316 pruebas; las únicas 2 que fallan son
  ajenas al cambio y propias del worktree (falta `toolchain/` para un fixture
  SDL y un SVG extraído con finales de línea CRLF).
- Evidencia histórica del PR original, anterior a estas correcciones ABI (no es aceptación del overlay revisado): runtime con el overlay (`build/kbd01-build`, 280 objetos, selftest y
  sonda de carga correctos): configuración inicial con ventana de apodo
  (`kbd01-applets-setup`, salida 0) y ruta de fotos de 540 s
  (`kbd01-applets-photo540`, salida 0, 32 332 frames, 0 errores de validación,
  2 fotos 1080×720 y 2 miniaturas 240×200 nuevas, auditoría `bytes-limpios` con
  evidencia completa, perfil original intacto). RTX 4060 únicamente.

## Límites

- La generación del runtime AMD se infiere de sus líneas de arranque; no hay
  hash ni versión del ejecutable de esa máquina.
- No se ha ejecutado la 0.5 en la RX 6900 XT: fotos, color y este paso siguen
  sin validar allí con el runtime correcto.
- El origen del teclado de Windows no está identificado.

## Qué falta para cerrar

1. Que la máquina AMD ejecute de verdad la 0.5 (LAUNCH-404 / AUTO-DATA) y
   repetir selección → evaluación → registro.
2. De esa sesión, la salida de `tools\triage_game_log.py`: debe decir
   «generación 0.5 o posterior».
3. Revisión de RTX tester del overlay y de la herramienta.
