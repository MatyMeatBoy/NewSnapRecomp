# Actualizar la misma instalación

La pestaña **Actualizar** consulta la última versión estable publicada en
`MatyMeatBoy/NewSnapRecomp`. El launcher instalado comprueba el canal al abrir;
también puedes pulsar **Buscar última estable**. Las versiones alpha y otras
prereleases quedan fuera de este canal. Si todavía no existe una estable, lo
indica sin elegir una alpha en su lugar.

El repositorio actual es privado. En **Acceso a repositorio privado…** puedes
guardar un token de GitHub de lectura con acceso a ese repositorio; permanece en
el Administrador de credenciales de Windows, fuera de GameData. También admite
`GH_TOKEN`/`GITHUB_TOKEN` o una sesión existente de GitHub CLI. El actualizador
distingue una estable ausente de un repositorio inaccesible. Las credenciales se
envían a la API canónica de GitHub y se retiran antes de seguir una redirección
de descarga hacia otro servidor.

**Descargar e instalar / reparar** sirve tanto para cambiar de versión como
para reinstalar la misma estable. Descarga y verifica el paquete antes de cerrar
el launcher. Un proceso de la carpeta temporal espera su cierre, instala los
archivos públicos y vuelve a abrirlo. Cierra la expedición antes de actualizar.
Si falla una sustitución, se restauran los archivos anteriores; si esa restauración
falla, se conservan los respaldos y se indica su ubicación. Esto no promete
recuperación automática ante un corte de energía.

## Tus datos y la versión del juego

Se conservan `GameData`/`newsnapGameData`, perfiles, partidas, ajustes INI y archivos
ajenos al paquete. El actualizador no descarga el juego ni sustituye su ejecutable
privado. La carpeta pública `profiles` contiene especificaciones de la versión
del juego, no las partidas del propietario.

Un launcher nuevo no convierte por sí solo el runtime privado 0.2 en el runtime
0.3. La pestaña muestra su compatibilidad y las capacidades que faltan. Si hace
falta recompilarlo, se reutilizan los datos importados; no es necesario volver
a dumpear el juego. Una compilación local puede reutilizar la generación y sus
objetos cuando su procedencia siga siendo válida; un cambio de instrucciones
requiere regenerar lo que corresponda.

La caché de shaders/pipelines depende de la GPU, el controlador y el traductor.
Después de trasladar la instalación, por ejemplo de NVIDIA a una RX 6900 XT,
usa **Preparar gráficos antes de jugar**. Que se reutilicen los datos importados
no significa que la caché de otro equipo sea compatible ni acredita una prueba
física en esa GPU.

## Alcance comprobado

Las pruebas automatizadas cubren selección del canal estable, integridad del ZIP,
inventario, rutas, archivos privados, reparación, conservación y rollback ante
errores de instalación. El supervisor se prueba con procesos Windows reales para
la espera y con sustitutos para instalación/reinicio. La aceptación del paquete
congelado y de una estable publicada se registra por separado antes de anunciar
la entrega como lista. La comprobación SHA-256 se apoya en HTTPS y el repositorio
canónico; no es una firma independiente del paquete.
