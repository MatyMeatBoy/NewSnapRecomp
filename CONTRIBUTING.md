# Coordinación de NewSnapRecomp

La rama de integración es `main`; el propietario pidió integrar/eliminar las
ramas auxiliares 0.4 y 0.5 y ahora recibir los PR de MatyMeatBoy. No recrear ramas
por versión. Los PR temáticos se preparan en un worktree aislado, sin cambiar
la rama del checkout compartido ni arrastrar cambios de otros responsables.

Leer **[docs/PENDIENTES.md](docs/PENDIENTES.md)** antes de editar. Tomar una tarea
LIBRE indicando responsable y archivos reservados. Respetar las reservas de
RTX tester/MatyMeatBoy y coordinar los puntos de integración compartidos.

La release 0.4 y sus artefactos/tag son inmutables. Por solicitud posterior del
propietario, se autoriza publicar 0.5 como alpha limitada, documentando aceptación
AMD/mando/FreeSync y picos de pacing pendientes. No presentar esos casos como
resueltos ni marcar la entrega como estable. No cambiar la lógica del juego
para saltar validaciones, progreso o tutoriales. Mantener el color/posprocesado
original de Snap y distinguir evidencia AMD RX 6900 XT de NVIDIA RTX 4060.

No modificar partidas, fotos, imports o claves del propietario. Usar copias en
`build/` para pruebas y no subir datos del juego ni ejecutables derivados.
Conservar cambios de otros agentes; pruebas GPU serializadas y comparaciones de
rendimiento con el mismo recorrido/resolución/estado de caché.

Cada autor puede commitear los archivos de su reserva en su rama de PR. El
coordinador RTX tester lleva la integración en `main` y la publicación. Para cerrar una
tarea, aportar causa, cambios, pruebas ejecutadas y límites; pedir revisión antes
de marcarla HECHA.
