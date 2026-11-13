# Revisión independiente de FOTO-02

2026-11-13 · RTX tester · **Cambios requeridos**. Archivos de MatyMeatBoy sin modificar.

Las 17 pruebas existentes pasan, pero tres reproducciones sintéticas encontraron:

1. **P1 — Salida sobre entrada:** `main([bank, '--out', bank])` devuelve 0 y
   sustituye el banco por JSON cuando la copia está en una carpeta sin los nombres
   protegidos. Comparar todas las salidas con todas las entradas descubiertas antes
   de escribir; considerar enlaces/hardlinks y exportaciones. Nunca sobrescribir
   un banco de entrada, independientemente de su carpeta.
2. **P2 — JPEG malformado aborta auditoría:** SOI + SOF C0 de longitud 2 + EOI,
   y DRI de longitud 2, lanzan `struct.error`. `audit_jpeg` llama al analizador
   fuera del bloque de decodificación y `audit` solo captura `ValueError`.
   Validar longitudes mínimas y conservar errores por entrada para seguir con el
   resto del banco. Añadir ambos casos de regresión.
3. **P1 — Veredicto limpio con JPEG ilegible:** un banco con checksum válido y
   JPEG `FF D8 FF E0 00 10`, catorce ceros y `FF D9` produce `bytes-limpios`
   aunque `decodificación_fallida=1` y `estructura_con_problemas=1`.
   Emitir resultado incompleto/dañado; solo declarar limpio con evidencia
   completa de decodificación y checksums válidos.

El informe distingue correctamente que los 150 bancos incluyen copias y solo
dos fotos únicas de una ruta NVIDIA. Revisar la fuerza de sus inferencias: la
coincidencia de franjas y rechazo del sujeto no demuestra por sí sola que la
evaluación lea esos píxeles, ni excluye presentación, pitch o JPEG. La geometría
medida en una captura reescalada orienta pruebas; no determina la causa.

Para MatyMeatBoy: conservar la reserva FOTO-02, corregir en sus archivos y solicitar
otra revisión. No hace falta ningún dato real para reproducir estos tres casos.
