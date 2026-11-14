# Pista para FOTO-01: imágenes de color enlazadas a la memoria del pool

2026-11-13 · Claude · **Hipótesis sin comprobar en AMD.** No toca archivos
reservados; es una observación para quien lleve FOTO-01.

> **Aviso (añadido tras recibir el log AMD):** el log cercano a la captura de
> las 22:39 sugiere un runtime anterior, sin hash que determine la identidad
> exacta (ver `keyboard-after-photo.md`). No se establece la versión de la
> captura de las 16:53. **Falta repetir con runtime identificado en AMD**.
> La hipótesis de abajo sigue siendo comprobable
> (el enlace de imágenes al pool no cambió entre versiones), pero lo primero es
> repetir la prueba con la 0.5 real.

## Observaciones nuevas

1. **El patrón de franjas es idéntico en dos fotos distintas.** La captura de
   las 16:53 (`codex-clipboard-b8af3c5e`) y la de las 22:39
   (`rx6900xt-0.5/album-bands-amd.png`) muestran contenido diferente pero las
   mismas celdas válidas y negras, en las mismas posiciones. Esto es compatible
   con disposición de memoria; una carrera o trabajo parcial determinista
   tampoco quedan excluidos. La medición de la primera captura está en
   `photo-bands-cpu.md` (15 franjas de ≈48 filas, tramos válidos contiguos).
2. **Una foto de Pikachu se ve completa en la pantalla de evaluación**
   (`evaluation-good-amd.png`). Falta comprobar identidad del slot/JPEG y las
   texturas concretas; la captura aislada no demuestra que sean los mismos bytes.
3. En RTX 4060 las transferencias de registro son de 1080×720 y 240×200 en
   formato 37 (RGBA8), sin diferencias fuente/buffer (trazas de Codex).

## Punto del código que encaja

`vk_texture.c`, `bind_pool_memory`: una imagen cuyo almacenamiento está en un
pool solo-GPU se **enlaza dentro de la memoria del pool**, en la dirección que
el juego le dio. El donor ya documenta el riesgo en RDNA2 (la familia de la
RX 6900 XT): el controlador pide para la imagen más bytes que su
almacenamiento NVN, y la cola cae sobre la siguiente textura del heap. La
guarda actual solo cubre profundidad/stencil:

```c
if ((e->f.depth || e->f.stencil) && req.size > guest_size) return 0;
```

El comentario del donor dice que las imágenes de color «se quedan en su sitio»
porque en una RX 9070 no se vio que la GPU escribiera el exceso. Eso no se ha
medido en RDNA2 ni con los tamaños de Snap (1080×720 y 240×200 no son tamaños
de Astral Chain). Si en la RX 6900 XT `req.size > guest_size` para una imagen
de color, dos `VkImage` quedan enlazadas a memoria solapada: Vulkan deja su
contenido indefinido en cuanto se escribe una, y el resultado sería justo un
patrón fijo en el orden de teselas del controlador.

## Cómo comprobarlo sin suponer nada

- **Medición (decisiva, barata):** registrar en cada intento de enlace
  `addr`, tamaño, formato, `req.size`, `req.alignment`, `guest_size` y si se
  enlazó. En NVIDIA dará la línea base; en AMD dirá si alguna imagen de color
  de la ruta de fotos excede su almacenamiento. Diagnóstico opt-in, sin cambiar
  comportamiento.
- **Experimento A/B:** un interruptor que no enlace ninguna imagen cuyo
  `req.size` supere `guest_size` (misma regla que profundidad, sin excepción por
  fabricante). La ruta alternativa «memoria propia» ya existe y se usa cuando
  falla la alineación o el tipo de memoria. Si las franjas desaparecen en AMD
  con el interruptor y vuelven sin él, la causa queda establecida.
- **Control en RTX:** forzar memoria propia para todas las imágenes de color y
  repetir la ruta de 540 s; valida que la alternativa no rompe fotos,
  evaluación ni tutorial antes de pedírselo al propietario.

## Límites

- No hay medición de `req.size` en AMD: la hipótesis puede ser falsa.
- No explica por sí sola el color saturado (COLOR-01).
- No se ha comprobado qué textura concreta usa la pantalla de selección.
