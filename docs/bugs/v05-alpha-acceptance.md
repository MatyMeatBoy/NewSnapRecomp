# Cierre de v0.5.0-alpha

[Release publicada](https://github.com/MatyMeatBoy/NewSnapRecomp/releases/tag/v0.5.0-alpha).
Fuentes/tag: `e314751d10f4c51e575443d0d72c466dc94980b7`.
La documentación de cierre posterior no cambia ese productor ni sus artefactos.
Entrega limitada autorizada: prerelease, no Latest estable; aceptación física
AMD RX 6900 XT/mando/FreeSync todavía pendiente.

## Verificaciones realizadas

- 299 pruebas Windows correctas y CI verde para el productor. Revisión de delta:
  entre dev1 y alpha solo cambian la versión y textos de metadatos Windows en
  los inputs de producción; API 3, capacidades y lógica de runtime intactas.
- Launcher público: 1103 archivos del manifiesto más manifiesto, hashes de todos
  los archivos y miembros del ZIP, CRC, exclusiones y 106 fingerprints verificados
  independientemente. Sprite original intacto; autotest congelado con PATH limpio
  correcto. Kit público: 7297 archivos del manifiesto más manifiesto, con la misma
  identidad, hashes/miembros/CRC y exclusiones verificados.
- Reconstrucción real desde el kit público final, con copias físicas independientes
  de ExeFS/RomFS y runtime anterior: generación nueva, 279 objetos y enlace
  correctos. Los dos probes CPU pasan, 14 hashes de runtime coinciden y la evaluación
  posterior no requiere otra reconstrucción. Inputs, perfil, configuración y
  runtime 0.4 originales intactos; sentinelas de la copia conservados.
- Runtime reconstruido SHA256:
  `e0dcac87a708d1f5f7c5a0cf880525784a8ae077f06c1b37c67f4166045b8db4`.
  Es privado y no se distribuye en GitHub.
- Ese ejecutable completó su propio ensayo normal de 540 s en RTX 4060, Original
  100 %, salida 0/frame 32083: dos fotos nuevas de Pikachu/Vivillon y dos miniaturas
  limpias. Bancos confirmados y transacciones coinciden; cuatro pares GPU exactos;
  evaluación del tutorial y primera expedición revisadas visualmente. Los 75
  archivos protegidos de perfil/respaldo siguen intactos. Async activado, 122 skips
  de pipeline y cero de traducción shader. No es un benchmark de rendimiento.
- Después de publicar: catálogo manual real, descarga/checksum/stage desde GitHub,
  instalación y reparación de la misma versión tras daño controlado del launcher.
  Se verifican los 1103 archivos, tres sentinelas y arranque con PATH limpio. El
  kit se descarga/extrae/verifica desde la release y se reutiliza sin red. Esta
  instalación usa datos sintéticos; la compilación del juego se acredita por el
  ensayo independiente anterior, no por esos sentinelas.
- Revisión remota: tag correcto, publicación no draft/prerelease, cuatro assets
  por nombre/tamaño/digest y notas UTF-8 exactas. El endpoint de última estable
  permanece sin estable: la alpha no dispara avisos automáticos. Tag y cuatro
  assets de 0.4 intactos.

## Artefactos públicos inmutables

| Asset | SHA256 |
| --- | --- |
| `NewSnapRecomp-0.5.0-alpha-windows-e314751d.zip` | `0b96dc37d261eb18f5c37d903c6a101f2763cad1f05d32410c4d678cd15f8f5a` |
| `NewSnapBuildKit-0.5.0-alpha-e314751d.zip` | `abc02b465885af99987a4f3b2c3f3a1fbcbc065768aba44f361dd3092f73411f` |

Sus dos sidecars `.zip.sha256` completan los cuatro assets. No se subieron
GameData, claves, fotos, perfiles, cachés, código generado del juego ni ejecutables
derivados del juego.

## Evidencia local y límites

Recibos privados bajo `build/`: `v05-alpha-public-artifact-review.json`,
`v05-alpha-public-kit-rebuild/verification.json`,
`v05-alpha-public-kit-photo540/acceptance.json`,
`v05-alpha-postpublish-smoke/verification.json` y
`v05-alpha-published-remote-review.json`.

La prueba no verifica AMD, todos los mandos, FreeSync, una ruta completa, todas
las escalas ni más de 60 FPS. El A/B del puente de recursos conserva su evidencia
separada y el pico local restante de 107,692 ms; no se declara eliminado todo el
stutter. No se regeneran fotos ya guardadas dañadas ni se modifica progreso,
evaluación de sujetos o tutorial. Ver el protocolo `v05-owner-validation.md`.
