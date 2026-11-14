# Aceptación del paquete 0.6.0-alpha

Productor cerrado: `8f4510ba4ab4613fe7597fd884f23245300931c5`.
Versión `0.6.0-alpha`, API 3 y nueve capacidades, incluida
`ieee-crc-slicing8`. Un commit posterior de este documento no cambia la identidad
de los artefactos ni atribuye los binarios a otro HEAD.

## Artefactos cerrados

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

## Puertas de aceptación pendientes

- **Auditoría independiente de artefactos:** revisión de los ZIP cerrados en
  curso. Añadir resultado y recibo al recibir el informe; no se declara aprobada
  por la sola presencia de sidecars o por la instalación del coordinador.
- **Funcional de 540 s:** sesión final en curso con el runtime reconstruido desde
  el kit. Falta cierre, revisión de fotos/miniaturas y recibo final. No se afirma
  aquí que esa aceptación haya terminado.
- **A/B CRC del candidato final:** pendiente de resultado aceptado y recibo.
  Las mediciones anteriores del helper no demuestran una mejora de FPS.

Las pruebas físicas de RX 6900 XT, FreeSync y mando y los síntomas AMD reportados
mantienen sus límites propios. La incorporación de CRC portable y la exportación
de logs no demuestran una corrección de fotos, color o vibración de cabeza.
No se publican juego, ejecutables derivados, fotos, partidas ni claves.
