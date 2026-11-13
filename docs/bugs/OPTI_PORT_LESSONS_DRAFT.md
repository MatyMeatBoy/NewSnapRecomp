# OptiPort · propuestas verificables desde NewSnapRecomp

**PROMOVIDO tras revisión:** commit OptiPort `9673006504bf6712b320da70965bc3f65f2dd41a` (2026-11-13). Las siete referencias revisadas se publicaron en el repositorio canónico y se instalaron en Codex; `SKILL.md` permanece idéntico. El checkout activo conservó su rama/HEAD y su índice; la copia de Claude, con cambios locales ajenos, se conservó sin sobrescribir. Recibo local: `build/optiport-lessons-candidate/promotion.json`. Las observaciones de revisión sobre el alcance del fixture de memoria y el roundtrip sin artefacto se corrigieron antes de promover.

**CANDIDATO AISLADO, pendiente de revisión de su diff.** Codex aprobó los siete
temas y sus límites. Los párrafos se materializaron en una copia bajo
`build/optiport-lessons-candidate/`, sin instalar ni publicar. No se
editó la skill instalada ni el checkout canónico. Mantener
las rutas y pruebas del proyecto aquí; promover únicamente los contratos
generalizables, sin contenido ni identificadores privados del propietario.

## Fuente y freshness

El 2026-11-13 se leyó la skill instalada y se ejecutó `git fetch origin main`
sobre el clon existente de [MatyMeatBoy/OptiPort](https://github.com/MatyMeatBoy/OptiPort).
`origin/HEAD` apunta a `origin/main`, cuya revisión comprobada es
`a948b71af2ead649b56f3cdc6e4190f77afda492`. El checkout permaneció en
`384fb79c132de3a4612ffd46d3c0a25a58adc561`: no hubo switch/reset, cambios de
archivos, nueva rama ni nuevo checkout. Fetch solo actualizó referencias remotas.

Se comparó la copia instalada con `git show origin/main:<ruta>`, normalizando
CRLF/LF. Coincidieron `SKILL.md` y estos siete módulos pertinentes:

- `references/graphics-memory.md`
- `references/runtime-adaptation.md`
- `references/reproduction-harnesses.md`
- `references/control-layouts.md`
- `references/profiling.md`
- `references/verified-lessons.md`
- `references/software-general.md`

No hay diferencia de contenido que sincronizar en esos archivos. No se afirma
que todos los módulos no utilizados de una instalación estén actualizados.

## Base de evidencia y límites

La [matriz local](GPU_MATRIX.md) conserva los dispositivos, binarios, ensayos y
resultados. Los contratos de color/import/storage/input tienen negativos y
positivos nativos; algunos cuentan además con observación NVIDIA. No existe
validación física AMD de las correcciones ni causa demostrada de sus franjas.

Los controles fotográficos normales de 540 s superados usan `f6d92250…` y
`06a8d9df…`, cada uno con su propia evidencia de proceso, transferencias y JPEG.
El segundo no se acredita por herencia del primero. Ni un rechazo de sujeto simultáneo ni
la apariencia periódica de una captura demuestran qué consumidor o copia falló.
No convertir 150 bancos duplicados en 150 fotos o recorridos independientes.

Las propuestas siguientes amplían secciones existentes; no duplicar todo el
método en `SKILL.md`. El orden recomendado es revisar contratos gráficos,
harness, entrada y procedencia, y finalmente añadir enlaces breves al catálogo.

## 1. Transferencia digital de color

**Destino:** `references/graphics-memory.md`, después de la tabla de
«Cerrar la cadena de recursos y coordenadas».

**Párrafos propuestos:**

> Separar los valores codificados de los píxeles, el formato base del recurso,
> la vista usada por su productor y la transferencia del destino. Un recurso
> con formato base sRGB puede haber sido escrito mediante un alias UNORM; una
> copia/blit que consulta el formato base puede decodificar otra vez bytes ya
> preparados para la pantalla. Corregir la frontera de transferencia demostrada,
> sin compensarla con saturación, contraste o gamma artística.
>
> La corrección depende también del destino: un swapchain sRGB aplica su propia
> codificación y puede convertir en doble encode una corrección válida para
> UNORM. Probar las clases fuente/destino realmente admitidas, swizzle, mips,
> capas, uso, barreras y vida útil de vistas compatibles; mantener separadas las
> rutas float/HDR y formatos cuyo contrato no se ha establecido. Comparar bytes
> digitales del mismo cuadro, tamaño y crop antes de atribuir diferencias a la
> pantalla. Una coincidencia exacta en una GPU no certifica las demás.

Referencia primaria añadida al candidato: [blit y conversión sRGB en Vulkan](https://docs.vulkan.org/refpages/latest/refpages/source/vkCmdBlitImage.html).

**Qué decide:** evita modificar el grade original y evita arreglar solo el caso
UNORM. El fallback sRGB-only fallaba en la primera propuesta y se corrigió tras
revisión. La matriz de formatos es CPU; la igualdad digital 1920×1080 es NVIDIA.

## 2. Memoria host importada y coherencia

**Destino:** `references/graphics-memory.md`, en «Presupuestar la memoria que
realmente se usa», después del párrafo sobre requisitos y ownership.

**Párrafos propuestos:**

> Cuando una API devuelve tipos compatibles o un selector tiene fallback,
> comprobar las propiedades del tipo finalmente elegido: compatibilidad de
> binding no garantiza visibilidad/coherencia para el acceso que hace el host.
> Documentar quién posee map/flush/invalidate, alineación, rangos y finalización
> GPU. La memoria importada por un puntero externo no hereda automáticamente el
> protocolo de una asignación gestionada por el runtime.
>
> Si el acceso directo exige coherencia que el tipo no ofrece, conservarlo solo
> donde el contrato se cumple y elegir almacenamiento gestionado con flush,
> invalidate y sincronización explícitos donde falte. Activar el fallback por
> capacidad real del recurso, no por vendor, ni desactivar globalmente una ruta
> válida. Inyectar tipos compatibles no coherentes, fallos de importación y un
> control coherente. El fixture demuestra esa política; atribuirle el fallo de
> una GPU exige observar su selección y sus transferencias reales.

Referencia primaria añadida al candidato: [importación de punteros host en Vulkan](https://docs.vulkan.org/refpages/latest/refpages/source/VkImportMemoryHostPointerInfoEXT.html).

**Qué decide:** el selector original devolvía un candidato no coherente pese a
la petición de propiedades. El fixture verifica flags, fallback por pool,
tracking y llamada invalidate controlada; `shadow_sync_pool` es un stub contador
y no valida flush, visibilidad GPU ni finalización. Las rutas existentes de
flush/barreras/fences se auditaron en fuente. El fallback no es un parche «si AMD»;
NVIDIA conserva su import coherente y el fallback físico sigue sin probarse.

## 3. Efectos funcionales de dibujos asíncronos

**Destino:** `references/runtime-adaptation.md`, al final de «Precarga gráfica:
cuatro unidades distintas», antes de «Procedencia transitiva…».

**Párrafos propuestos:**

> Antes de permitir omitir trabajo gráfico mientras se compila un pipeline,
> establecer sus efectos observables. Un draw puede escribir SSBO o imágenes
> storage que leen captura, evaluación, simulación o exportación; un render
> target reciente no convierte esas escrituras en opcionales. Si la reflexión
> requiere terminar una traducción todavía pendiente, no clasificar la etapa
> desconocida como pura. Distinguir escritura real de lectura sola y de flags
> de coherencia que no implican store.
>
> Para operaciones obligatorias, usar el contrato real de espera/publicación
> del pipeline, incluidos trabajos ya encolados y timeouts parciales. Un wrapper
> llamado síncrono puede retornar pending si no se solicita esperar. Conservar
> el error terminal y distinguirlo de «aún pendiente»; agotar un tramo de espera
> no autoriza descartar la operación requerida. Una cancelación o un error
> controlado deben abortar la operación o sesión según su contrato, con limpieza
> acotada; no simular éxito parcial ni continuar consumiendo datos ausentes.
> Mantener async y sus políticas
> válidas para trabajo que sí sea opcional. Auditar por separado dispatch compute:
> no trasladar automáticamente a él una hipótesis sobre draws gráficos.

**Qué decide:** conserva efectos sin apagar async globalmente. El fixture falla
antes y pasa después en preflight/reflection/wait; el uso real de la clase SSBO
no identifica todavía una foto o mira concreta del reporte.

## 4. El observador puede cambiar la ejecución

**Destino:** `references/reproduction-harnesses.md`, después del control
negativo/positivo; enlace desde «Vista profunda de tirones» en `profiling.md`.

**Párrafos propuestos:**

> Comprobar si screenshot, headless, trazas o modo determinista cambian async,
> esperas, temporización, cachés o capturas del producto. Registrar la política
> efectiva desde el código y el proceso ejecutado; una inicialización llamada
> no prueba que su consulta de estado siga habilitada. Una imagen diagnóstica
> correcta no valida una ruta normal que omite trabajo por compilación pendiente.
> Separar equivalencia visual, aceptación funcional y medición de rendimiento.
>
> Restaurar para cada control una copia identificada del mismo estado inicial,
> incluidas variantes transaccionales/backups cuando el producto puede recuperar
> de ellas. Registrar hashes y generación; no editar progreso para forzar el
> checkpoint. Para una cadena imagen → buffer → codificador → miniatura →
> selección/evaluación, observar cada frontera y repetir el consumidor original.
> Un JPEG limpio no prueba identificación; un thumbnail corrupto y un rechazo
> simultáneos no prueban causalidad. Contar contenido único, no copias del banco.

**Qué decide:** `--shot` cambia la política efectiva de async en este runtime.
Los controles normales restauraron el mismo backup y completaron el flujo sin
flags/puntuaciones falsos. La auditoría de JPEG no debe usarse como sustituto de
la aceptación original ni de una prueba del binario final.

## 5. Continuidad de entrada y configuración concurrente

**Destino:** `references/control-layouts.md`, nueva subsección después de
«Cambio de dispositivo y presentación», antes de «Validación pertinente».

**Párrafos propuestos:**

> Una muestra relativa retenida por cuadro debe pertenecer también a la
> generación de captura/dispositivo que la produjo. Liberar y recapturar entre
> dos polls puede ocurrir sin cambiar el frame: un booleano observado al final
> no revela la discontinuidad. Propagar un epoch desde el dueño de la captura
> e invalidar muestras anteriores. Probar reposo, delta conocido, mismo frame,
> foco perdido/recuperado y cuadro detenido, conservando sensibilidad y binding.
>
> Reiniciar muestras/orientación fusionadas al cambiar o perder fuente, apagar
> sensores o interrumpirse su lectura según el contrato. Comprobar el ajuste
> antes de habilitar hardware y revertir habilitaciones parciales; una prueba
> mock no debe encender sensores físicos. No duplicar con estáticos no atómicos
> una configuración live que ya se publica de forma segura: una lectura antigua
> puede terminar después de la nueva y dejar un valor viejo bajo una versión
> nueva. Reproducir esa intercalación con hilos coordinados y comprobar el estado
> posterior, no solo el valor devuelto por cada lector.

**Qué decide:** se demostraron muestras retenidas, fusión heredada y una carrera
real del caché `on/seen`. El mecanismo no autoriza recentrar el HUD ni aumentar
deadzone para ocultar drift físico no medido. Una vista de mando por posiciones
físicas tampoco debe prometer el binding efectivo del juego.

## 6. Procedencia del productor y reutilización segura

**Destino:** `references/runtime-adaptation.md`, «Procedencia transitiva de
importaciones y código generado», después del primer párrafo; referencia desde
«Memoria y caché» en `references/software-general.md`.

**Párrafos propuestos:**

> Identificar también el entorno y las dependencias que ejecuta el productor,
> no las que se recuerdan por nombre. Si un loader usa un descompresor externo,
> su identidad pertinente debe formar parte de la receta reutilizable junto a
> intérprete, generador y flags. Un módulo adicional en disco puede cambiar el
> layout aunque no esté en el manifiesto: rechazar entradas inesperadas que
> consume el generador o verificarlas e incluirlas en la identidad antes del hit.
>
> Una copia de caché debe ser independiente y verificarse después de copiar;
> comprobar solo el origen no detecta una copia alterada. Limitar entradas y
> bytes, validar ownership y rutas resueltas, y rechazar symlinks/reparse points
> antes de limpieza recursiva. No convertir un objeto desconocido en propiedad
> del caché para cumplir el presupuesto. Corrupto/no disponible implica miss y
> generación fresca; no reutilizar ejecutables/objetos nativos solo porque sus
> fuentes generadas pasaron. Verificar originales también en la ruta caliente.

**Qué decide:** la revisión detectó LZ4 omitido y módulos ExeFS extra que cambiaban
layout sin cambiar clave; ambos se corrigieron con regresiones. El ensayo real
midió 86,820 s de generación frente a 3,044 s de restore + 0,265 s de verificación,
con salidas idénticas. Es tiempo de preparación; no es una medición de FPS.

## 7. Resumen medido sin ocultar resultados adversos

**Destino:** `references/profiling.md`, al final del párrafo de percentiles.

**Párrafo propuesto:**

> Mantener el recorrido completo como resultado principal si fue la ventana
> acordada. Un segmento posterior puede diagnosticar calentamiento, pero no
> reemplaza una cola completa peor ni convierte resultados mixtos en ganancia
> global. Conservar denominadores, repeticiones y actividad concurrente; separar
> generación, compilación/prewarm, tiempo de entrada, intervalos de juego,
> presentación y GPU busy. Una mejora de caché de build no acredita más FPS, y
> un contador de espera cero no identifica por exclusión todos los picos restantes.

**Qué decide:** el A/B completo tiene media equivalente y p99 nuevo peor; no se
promociona como optimización global. Una corrida por binario tampoco permite
atribuir una diferencia de inicio a una causa confirmada.

## Catálogo de lecciones propuesto

**Destino:** `references/verified-lessons.md`, filas nuevas con enlaces internos
a los módulos anteriores; evitar incorporar rutas/builds/fotos privadas.

| Disparador | Mecanismo y comprobación útil | Límite que debe acompañarlo |
| --- | --- | --- |
| SDR cambia contraste al presentar | Fuente base/vista y transferencia del destino no coinciden; matriz de clases y comparación de bytes del mismo cuadro. | No valida monitor/HDR/otra GPU. |
| Import host acepta memoria no coherente | Un selector compatible relajó propiedades necesarias; verificar flags reales y fallback gestionado por capacidad. | No atribuir a un vendor sin traza del recurso. |
| Draw omitido pierde datos funcionales | Storage escrito hace obligatorio el draw aunque su color pueda descartarse; reflection y espera real de pipeline. | Fixture de preflight no identifica el draw del reporte. |
| Captura de diagnóstico pasa y modo normal falla | El observador cambia async o estado inicial; control normal y backup equivalente. | No editar progreso ni confundir foto visible con evaluación aceptada. |
| Cámara conserva movimiento tras recaptura | Muestra por frame sin identidad de captura; epoch e invalidación de fuente/fusión. | Drift físico y puntería libre requieren medición distinta. |
| Ajuste live queda viejo tras cambio | Caché redundante compartida mezcla valor viejo/versión nueva; prueba de dos lectores intercalados. | Revisar la seguridad del proveedor de configuración antes de eliminar la caché. |
| Caché reutiliza receta incompleta | Dependencia ejecutada o módulo adicional fuera de clave; verificar consumidor, entorno e inventario real. | Ahorro de generación no mide gameplay ni certifica SDK. |

## Revisión antes de promover

El coordinador debe comprobar que cada párrafo cambia una decisión ya cubierta
por evidencia, resolver duplicados con upstream y revisar la matriz de límites.
La promoción posterior necesita revisión de su diff concreto; este borrador no
sincroniza ni publica la skill. No transportar cifras, umbrales, formatos o
políticas específicas del juego como defaults universales.

## Aplicación aislada de los párrafos aprobados

La copia conserva `baseline.json` de los ocho archivos leídos en `a948b71`.
`SKILL.md` y su frontmatter son idénticos al upstream; el candidato cambia solo
las siete referencias existentes. Se añadieron copias de contexto Markdown y
LICENSE del mismo commit para validar los enlaces; no son cambios propuestos.

Artefactos locales de revisión:

- [Diff unificado](../../build/optiport-lessons-candidate/lessons.diff).
- [Archivos y hashes](../../build/optiport-lessons-candidate/changed-files.json).
- [Validación](../../build/optiport-lessons-candidate/validation.json).
- [Oráculos y límites](../../build/optiport-lessons-candidate/VALIDATION.md).

Reejecución CPU pertinente: 40 pruebas de color/readback/storage/input/cache
pasaron. RED→GREEN se vincula a los oráculos nativos y controles ya observados,
incluidos los once fallos baseline de entrada y el preflight gráfico que cambia
de exit 1 a exit 0. Esto acredita los mecanismos que motivan el texto; no se
afirma una prueba conductual de cumplimiento de agentes con la redacción nueva.
La revisión independiente del candidato y su eventual instalación/promoción
permanecen a cargo del coordinador. No hubo nueva prueba GPU ni edición global.

La revisión posterior acotó la evidencia de importación: el fixture de la sombra
no acredita flush/finalización GPU. También se retiró de la matriz la afirmación
de roundtrip de 256 códigos, al no acompañarla un artefacto guardado. La revisión
añade las referencias primarias Khronos y el contrato de cancelación/error sin
éxito parcial; conserva el log CPU previo, sin repetir tests por cambios de texto.
