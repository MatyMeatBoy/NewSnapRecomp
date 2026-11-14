# Aceptación del paquete 0.6.0-alpha

Productor final cerrado: `82e01064d673a0489304913575ec646da148887c`.
El candidato privado anterior `8f4510ba4ab4613fe7597fd884f23245300931c5`
no se publicó: la revisión detectó bytecode con ruta local y tres headers SDK
sin pin, ajenos al runtime. Se conservó intacto y se corrigió el productor.
Las secciones históricas siguientes documentan ese candidato y sus consumidores;
la identidad final se detalla separadamente.
Versión `0.6.0-alpha`, API 3 y nueve capacidades, incluida
`ieee-crc-slicing8`. Un commit posterior de este documento no cambia la identidad
de los artefactos ni atribuye los binarios a otro HEAD.

## Candidato privado anterior, conservado e inmutable

| Archivo | Bytes | SHA256 registrado en su sidecar |
|---|---:|---|
| NewSnapRecomp-0.6.0-alpha-windows-8f4510ba.zip | 285965741 | 3e6b1d94531f6c5b7bce5f77aa14dbbb388dfc7cabbf0dc4a05dee0b73bdb8da |
| NewSnapBuildKit-0.6.0-alpha-8f4510ba.zip | 253134472 | 84c2a1579cf871f518739bcee7c76ef557bc196995912c8288f849565892f40b |

Ambos tienen su archivo ASCII `<nombre>.zip.sha256`, de 114 y 108 bytes,
respectivamente. El paquete Windows contiene el kit y su sidecar bajo
`build-kits/`, fijados por el manifiesto exterior. Estos bytes están cerrados;
la comprobación independiente completa de inventarios, hashes, límites y pins
anidados se registra como pendiente más abajo, sin anticipar su resultado.

## Fuente y consumidores reales verificados

La suite en fuente registra 411 casos, resultado OK y una omisión por permisos
de symlink (`build/v06-full-tests.log`, 73,362 s). CI del productor también pasa.
Esto no equivale a aceptación física de todas las GPU ni de los recorridos del
juego.

La instalación aislada usa los ZIP cerrados y el consumidor real del updater:
stage, instalación, reparación de la misma versión y comprobación de los 1.105
archivos del manifiesto. El kit incluido se adquiere y reutiliza con las llamadas
de red prohibidas por la prueba. Se conservan los dos sentinelas sintéticos:
guardado y configuración INI legada. Los archivos públicos permanecen sin cambios.

La reconstrucción se ejecutó mediante Python 3.14.9 portable del kit, sin reutilizar
generación previa: 106 chunks main y 37 SDK, 143/143 emitidos. El log registra
283 objetos verificados, cero recompilaciones por discrepancia de hash y enlace
completo; compilación de 115,3 s y enlace de 0,8 s. La generación registrada tarda
28,559 s. El worker ejecuta `--selftest` y `--probe-loader` antes de activar el
candidato; el flujo completo terminó y la evaluación posterior devuelve
`needs_rebuild: false`.

SHA256 del runtime reconstruido y activado:
`018d87d6485fcdd6261a099af2a9fc6bd2272b165e63a13afefd8640a9a58a7f`.
Su marcador coincide con versión, revisión, API y nueve capacidades del launcher.
El ejecutable derivado queda en la copia privada de aceptación, no en los assets
públicos.

Evidencia privada principal: `build/v06-offline-package/verification.json`,
`build/v06-offline-package.log` y
`build/v06-offline-package/installed/GameData/logs/runtime-rebuild.log`.
ExeFS se copió; RomFS es un hardlink a una copia privada independiente anterior y
se usó solo en lectura. No se modifica la instalación original 0.4 ni los assets
publicados de 0.4, 0.5 o 0.5.1.

## Launcher congelado y exportación de diagnóstico

Comprobación independiente del launcher instalado real:
`NewSnapLauncher.exe --selftest-launcher`, con `PATH=C:\Windows\System32` y
sin variables `PYTHON*`. Salida 0 en 1,703 s; el log vacío es el comportamiento
esperado del selftest windowed, que construye y destruye una ventana Tk retirada
en un proyecto temporal. No quedaron procesos del ejecutable instalado antes ni
después. No se inició una sesión normal del juego ni GPU.

El hash del launcher coincide con su pin del manifiesto:
`dea4938760a72def32b66678da880251b46bd06dd4364d31f665cee6d4f9f25b`.
Recibos privados: `build/v06-frozen-selftest.json` y
`build/v06-frozen-selftest.log`.

La prueba real de exportación desde la GUI congelada usa una copia aislada con
600 entradas ajenas antes del log reciente. El ZIP incluye ese log, resumen y
análisis JSON; las rutas y secretos de la fixture están redactados y los archivos
fuente se conservan. El recibo `build/v06-frozen-ui-verification.json` declara
`frozen_ui_export_pass: true` y el ZIP de diagnóstico tiene SHA256
`15d23bcfe6d5a5ce918f63742ee52a1ced488eb3ef9ffb5cfb3ff1d963db12b9`.
Ese ZIP sintético permanece privado.

## Cierre de las comprobaciones del candidato nativo

- **Auditoría anterior:** detectó las dos anomalías descritas al principio;
  `build/v06-independent-artifacts.json` conserva ese resultado y esos ZIP no
  se publicaron. No se sobrescribieron al corregirlos.
- **Funcional de 540 s:** completada con el SHA nativo indicado arriba, RTX4060,
  salida0/boot passed/sin fatal/33 capturas. Se observaron evaluación de Pikachu
  y Vivillon y primera expedición, sin alterar lógica o progreso del tutorial.
  La auditoría guardada comprueba dos fotos1080×720 y dos miniaturas240×200:
  checksum, estructura y decodificación válidos, sin bandas/bloques detectados.
  Los archivos originales protegidos conservan sus hashes. Evidencia privada
  `build/v06-final-photo540/{run.json,photo-audit.json}`.
- **A/B CRC:** dos warmups y dos pares inversos de20s, mismo SHA, perfiles/ruta
  iguales, cachés restauradas, Original100%, FIFO1920×1080, AC1/saver0. Revisión
  independiente reproduce métricas: p99 agrupado39,903→32,037ms, mediana
  16,651→16,652ms. El máximo empeora en el segundo par y la fase posterior al
  frame600 no mejora uniformemente. No demuestra pacing perfecto ni más FPS.
  `build/v06-crc-ab-fullscreen/comparison.json`, valid-complete. El primer ensayo
  con ventana1920×1055 quedó excluido y conservado, sin mezclar sus medidas.

## Artefactos finales corregidos, productor82e01064

| Archivo | Bytes | SHA256 |
|---|---:|---|
| NewSnapRecomp-0.6.0-alpha-windows-82e01064.zip | 285940050 | 6ff10edccd90b0cbb4e279e348afe30b9b174545873dff3dde2e9e1228c23e6b |
| NewSnapBuildKit-0.6.0-alpha-82e01064.zip | 253111153 | 55a94faaa918e1763fa63acf1461e539fcf691f300963d34034c8c1cf564d5f5 |

Auditoría independiente **PASS sin hallazgos**:
`build/v06-r1-independent-artifacts.json`. Inventarios1105/7310 archivos,
sidecars, kit anidado y114 fingerprints comunes coinciden. Los788 archivos de
fuente concuerdan con productor/donante fijados (14 diferencias solo CRLF);
diez archivos vendor y dos recibos canónicos verificados. Sin bytecode Python,
extras SDK ni fuentes desconocidas.

Los7309 archivos comunes de ambos kits son idénticos. Solo se retiraron el pyc
y los tres headers sin uso, y se añadió un recibo FSR canónico. Las recetas,
toolchain, headers/DLL requeridos y shader nativo son idénticos. El launcher
final SHA `c9a627c21fbd61ed3a770511d9794c67bede9412b4cc8c0c8dcf0414ce59cb2a`
es idéntico al probado salvo COFF/debug timestamps y checksum PE, demostrado
comparando ambos ZIPs y normalizando únicamente esos campos tipados. Su PYZ y
todo el código del ejecutable permanecen idénticos; evidencia privada
`build/v06-r1-frozen-equivalence.json` y revisión independiente.

La suite final82e01064 pasa416 pruebas en83,627s (una omisión symlink), y su CI
pasa. Instalación/reparación y adquisición offline del ZIP final pasan:
1105 hashes, dos sentinelas y todos los archivos públicos conservados. El kit
genera143 chunks desde cero con Python3.14.9, compila283 objetos en112,1s y
enlaza en0,7s; probes/activación pasan y la evaluación no pide reconstruir.
Recibo privado `build/v06-r1-offline-package/verification.json`.

Runtime final derivado, productor82e01064:
`24c014a53d76ad86c7002f697aeb0d4f717d6535b0113a9319a65dc1dc59cec9`.
Es distinto al binario8f4510b: no se presenta como identidad bit a bit. Los
inputs nativos comunes son idénticos según el inventario independiente; la
prueba larga y el A/B conservan explícitamente el productor y SHA anteriores.
Una sesión adicional real de60s con el SHA final carga una copia del perfil
posterior al tutorial y continúa el diálogo: exit0/boot passed/sin fatal,
cinco capturas y originales protegidos intactos. No es otro A/B ni recorrido
fotográfico completo; `build/v06-r1-final-expedition60/run.json`.

El launcher final instalado repite selftest con PATH solo System32 y sin
variables PYTHON: salida0 en0,828s, sin procesos propios restantes;
`build/v06-r1-frozen-selftest.json`. La equivalencia tipada del launcher permite
conservar la prueba GUI anterior del exportador; no se atribuye al binario final
una segunda exportación que no se ejecutó.

Las pruebas físicas de RX 6900 XT, FreeSync y mando y los síntomas AMD reportados
mantienen sus límites propios. La incorporación de CRC portable y la exportación
de logs no demuestran una corrección de fotos, color o vibración de cabeza.
No se publican juego, ejecutables derivados, fotos, partidas ni claves.
