# Candidato privado 0.5.0-dev.1

Productor: `555d6258d982b0fd5ab3432bc1f1d9f7c6224c1c`.
Ejecutable SHA256: `76f08005b1ffca903e5cab8fdaa5b2f46fe48c818499cd8cc2e51a7885bb527a`.
No hay tag ni publicación 0.5. La release 0.4 permanece inmutable.

## Verificación

- Suite Windows: 299 pruebas correctas. Después del ajuste del directorio de
  pruebas en un checkout limpio, diez pruebas RNG correctas; CI Linux verde
  para el productor final. Los casos privados o exclusivos de Windows no se
  convierten en aceptación física Linux/AMD por ese resultado.
- Compilación nativa: generación y 279 objetos verificados, enlace correcto;
  fuentes limpias e identidad registrada antes/después. Launcher congelado:
  1103 archivos del manifiesto y ZIP verificados, huellas iguales a las fuentes,
  sprite original intacto y arranque de prueba con PATH mínimo correcto.
- Instalación y reparación sobre la misma versión: 1104 archivos reemplazados
  en cada operación sobre una instalación aislada; tres sentinelas de datos,
  configuración y preferencias conservados. Arranque del launcher reparado OK.
- Cierre privado: 15 archivos de runtime incluido marcador nuevo; probes
  `--selftest` y `--probe-loader` correctos. Las identidades de launcher, kit y
  runtime coinciden. La evaluación aislada no requiere reconstrucción; adquisición
  del kit local exacto con inventario verificado y cero solicitudes de red.

## Fotografías del ejecutable final

Ejecución normal de 540 s en RTX 4060, sin `--shot`, Original y escala 100 %;
`AC_SNAP_RANDOM_RANGE=1`. Salida 0, frame final 32302. El perfil se copia desde
un respaldo inicial sin fotos; nunca se edita progreso ni lógica del juego.

Dos fotos nuevas (Pikachu y Vivillon) de 1080×720 y dos miniaturas de 240×200,
sin filas negras y revisadas visualmente. Los bancos confirmados y transacción
coinciden. Cuatro pares GPU fuente/buffer son idénticos byte por byte; la diferencia
JPEG es la compresión esperada, no una comparación byteidéntica del JPEG.

Se observaron la evaluación/tutorial posterior y la primera expedición. Los 75
archivos protegidos de perfil/respaldo permanecieron intactos. Hubo 103 skips de
pipelines gráficos y cero skips de traducción shader; no se desactivó async global.
Empaquetado, reparación y probes CPU concurrentes: este ensayo no mide rendimiento.

Las muestras de enfoque `cpu-read-01-f13180-source.png` y
`cpu-read-02-f13777-source.png` muestran la retícula/nombre legibles en 1920×1080,
sin las franjas del reporte. Son dos controles visuales locales; no certifican
todo el movimiento/zoom ni la ruta física AMD.

Evidencia privada: `build/v05-rng-positive-control-normal540/acceptance.json`,
`photo-evidence.json`, `profile-guard.json`, capturas y bancos. El A/B de rendimiento
separado está documentado en `cpu-asset-workers.md` y `GPU_MATRIX.md`.

## Puerta física pendiente

No se han validado los reportes en la RX 6900 XT, su mando, monitor ni FreeSync.
Retícula en movimiento/zoom, cámara en reposo/reconexión, color y fotos se verifican
con el protocolo `v05-owner-validation.md`. Persiste un pico local aislado de
107,692 ms en el A/B; no se declara eliminado todo el stutter.

Los paquetes privados no contienen imports, claves ni perfiles del propietario.
El runtime recompilado sí contiene código derivado del juego: no subirlo a GitHub.
El kit y el launcher conservan sus inventarios públicos separados. Usar una copia
completa de GameData y verificar también la ruta del perfil en Home antes de jugar.

Paquete local de prueba:
`build/NewSnapValidation-0.5.0-dev.1-555d6258-private.zip`.
SHA256 `779fc5a90d2551e4c62bcabc30ed9f5dd534f50304917c493e290d23187f07bf`.
Contiene 8420 archivos: launcher 1104, runtime privado 15, kit 7298 e instrucciones
3. Inventarios, copias independientes, identidad triple, tamaños y CRC del ZIP
verificados. El comando de inicio solo selecciona el kit local y abre el launcher;
las instrucciones exigen copiar datos/perfil y comprobar sus rutas antes de lanzar.
