# Verificación de los artefactos 0.5.1-alpha

Productor: e77393f4808ce558787a7381454ccbfe2dab345d. API 3, ocho capacidades,
versión 0.5.1-alpha. Los commits posteriores de documentación/herramientas de
análisis no cambian esa identidad ni atribuyen estos binarios a otro HEAD.

| Artefacto cerrado | Tamaño | SHA256 |
|---|---:|---|
| NewSnapRecomp-0.5.1-alpha-windows-e77393f4.zip | 285947743 | b812819005fc0eb67fff1a292d3b8b93d08c076b110ae3c47a3c96a1b30ea3e8 |
| NewSnapBuildKit-0.5.1-alpha-e77393f4.zip | 253117747 | 88845de14818b53519f22859e8b9f9cf6c2b93da80ebef9d33125bfef818b965 |

Checksums ASCII respectivos incluidos. Revisión independiente: todos los
1.105 archivos del manifiesto Windows y 7.308 del kit, inventario exacto, hashes,
raíces, límites, exclusiones de datos del propietario y ausencia de enlaces.
El ZIP del kit y sidecar anidados coinciden con los independientes; 109
fingerprints comunes coinciden entre freeze y kit. El parser del updater acepta
el paquete y el selector heredado identifica un único asset Windows.

## Consumidores reales

- Stage e instalación con los ZIP cerrados; reparación de la misma versión y
  comprobación de todos los hashes. Dos sentinelas sintéticos conservados.
- Adquisición y reutilización del kit incluido con llamadas de red prohibidas
  por la prueba. Recompilación mediante Python 3.14.9 portable de ese kit:
  143 chunks nuevos, 280 objetos compilados, probes CPU/loader y activación
  correctos. La evaluación posterior no requiere reconstruir otra vez.
- Runtime resultante: SHA256
  7af250585180f2beac30053c1d463c4ae269232b8532ff96b6045c307ba20e70.
- Autotest del launcher instalado con PATH del sistema y sin Python externo.
  GUI congelada revisada: Inicio sin selector, perfiles en Juego, presets y
  tooltips. Exportación real desde copia aislada con log sintético produce ZIP
  válido, resumen, texto y análisis JSON; no modifica el staging público.
- Dos sesiones Vulkan de 20 s en RTX 4060, FIFO y Mailbox: salida 0/boot passed,
  modo solicitado/efectivo y cuatro categorías observadas; 32 líneas de traza
  por sesión, INI legado intacto. Son aceptación de telemetría; no un A/B de
  rendimiento ni prueba de FreeSync/AMD. Sin candidatos de pool excesivo en
  esas dos sesiones; no permite descartar la hipótesis en la ruta de fotos.

Evidencia privada: build/v051-independent-artifacts.json,
build/v051-offline-package/verification.json, clean-path-launcher.json,
build/v051-frozen-ui-verification.json y build/v051-final-trace-smoke/verification.json.
ExeFS se copió a la instalación sintética; RomFS es un hardlink a una copia
privada independiente anterior, usada solo en lectura. Instalación original
newsnapGameData y assets publicados de 0.4/0.5 no se cambian.

387 pruebas previas al cambio de identidad y 80 focalizadas posteriores pasan,
una omitida por privilegios symlink. CI del productor e77393f también pasa.

## Límites y estado

Falta aceptación física RX 6900 XT/FreeSync/mando, fotos/miniaturas/color
reportados y cabeza de la intro. El overlay de applets del PR #2 continúa en
revisión por contratos ABI/resultados y no forma parte de esta entrega.
La investigación del PR #3 es tooling/documentación, no corrección de animación.
No se publica juego, ejecutable derivado, fotos, partidas ni claves.

## Cierre remoto posterior

Publicada https://github.com/MatyMeatBoy/NewSnapRecomp/releases/tag/v0.5.1-alpha.
Tag remoto resuelve exactamente e77393f4, draft=false y prerelease=true; se
publicó con Latest=false. Los cuatro assets remotos coinciden por tamaño/digest,
incluidos ambos sidecars. El consumidor real del updater descargó el asset
Windows publicado y validó stage/manifiesto de 1.105 archivos. El catálogo manual
elige 0.5.1-alpha; el filtro automático stable lo excluye (no hay stable disponible).
Evidencia privada build/v051-published-smoke/verification.json.

El PR #3 se integró después en main junto con correcciones de segmentos/paridad
y conclusiones: solo tooling, tests y documentación; no cambia el productor
cerrado e77393f4 ni se reescriben paquetes. El PR #2 sigue abierto para el overlay.
