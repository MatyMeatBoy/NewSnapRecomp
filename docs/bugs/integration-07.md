# Integración posterior a 0.6: verificación local

2026-11-14. PR 6, 7, 8, 9 y 10 integrados en main. No es una release nueva:
los assets/tag 0.6 publicados conservan sus bytes. El nuevo kit público y la
aceptación física AMD siguen pendientes.

## Cambios y evidencia

- Mantenimiento: hashes e inventario del runtime y ausencia de las cinco rutas
  de caché se comprueban antes del commit. Recuperación verifica lo restaurado
  antes de descartar el backup; copia sin enlaces/junctions anidados. PR 7 y
  revisión independiente. Ver runtime-replacement-verification.md.
- Fotos: diagnóstico acotado y best-effort, sin PNG por defecto, máximo 24
  capturas y 64 MiB de payload pendiente. Se conservaron las importaciones por
  defecto; shadow sigue opt-in. PR 6 con correcciones de revisión. Esto no cierra
  las bandas ni los faults de RX 6900 XT.
- Traductor: BFE/BFI/SHF definidos, originales 12 parches preservados,14 exactos.
  655.360 casos bitfield y262.080 casos de funnel shift pasan sobre métodos C# reales. NativeAOT
  compilado normalmente;18 sintéticos públicos pasan Vulkan 1.2 y coinciden byte
  a byte con el traductor managed. Pin binario e ID verificados antes de build,
  copia y empaquetado. PR 9 y revisión independiente; ver xlate-semantics.md.
- Vídeo: una sola superficie desplazable, sin Básico/Avanzado. Todos los
  controles, preset, presentación, pantalla completa, tooltips y callbacks se
  conservaron. Comprobación Tk oculta:1 canvas, 0 notebooks internos,11 comboboxes
  con tooltips, preset Ultra/Personalizado y persistencia correctos. Revisión AST
  independiente y CI del PR 10 aprobados. Sin nueva inspección visual interactiva.

Suite completa Windows tras integrar PR 9:465 pruebas, 1 omisión, 86,540 s, salida 0.
Incluye pruebas nativas con los headers/compiler reales, .NET 10 y validador
SPIR-V. El PR 10 cambia solo la disposición de widgets; además de su revisión y
comprobación Tk, sus dos ejecuciones CI completas pasan.

Runtime privado compilado desde PR 9 head b593c2d800026a4e1a05224d8dca8f2441ae1258,
que ya incluye PR 6/7/8: selftest y probe-loader pasan. Su SHA256 es
`d66ad3f413cf8c043fc726ee1751a80cc71809d97e49c7977a92d8f9c4f19763`.
La instalación de ese candidato real sobre fixture independiente confirma
hashes, eliminación de las cinco cachés y backup, conservando sentinelas
sintéticos de perfil y grabaciones. Ninguna partida/foto/import original fue
modificada. Artefactos y recibos quedan privados en build/integration-07/.
La compilación y los probes son CPU; no acreditan gameplay ni estabilidad AMD.

## Reporte nuevo RX 6900 XT con shadow

El tercer log del propietario confirma shadow activo pese al aviso de clave
SHADOW desconocida. Aun así termina con otra escritura GPU inválida; el último
modo temporal registrado era FSR 4 Native AA. Eso refuta que activar shadow baste
para evitar ese cierre en ese recorrido/runtime. No comprueba el aspecto de las
fotos: no contiene el diagnóstico de PR 6 ni imágenes nuevas. Tampoco acredita
que FSR 4, sus cambios, SMAA o la importación causen el fault. El traductor que
registra es anterior al nuevo pin, y no identifica este nuevo ejecutable privado.

También registra que no reconoce el punto de SMAA y mantiene SMAA sobre el AA
temporal: pista separada para investigar, no causa confirmada del cierre.
Log original, copia idéntica, SHA y análisis detallado permanecen en build/;
no se sube el log privado. FOTO-01 y QA-AMD-01 siguen abiertos.

La prueba interactiva del launcher fue detenida con Escape. No se reanudó
control de ventanas ni se ejecutó una prueba GPU concurrente con Claude.
