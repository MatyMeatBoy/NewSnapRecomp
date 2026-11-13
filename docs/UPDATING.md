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
ajenos al paquete. El actualizador público no descarga el juego. La carpeta
pública `profiles` contiene especificaciones de la versión del juego, no partidas.

Desde la 0.4, si el runtime no coincide con la versión, capacidades, hashes o
receta del launcher, se reconstruye localmente con tus datos importados. No hace
falta volver a dumpear el juego ni instalar Python o un compilador. El kit de
herramientas se descarga de la misma versión y revisión exacta del launcher;
se verifica su SHA-256 y cada archivo antes de ejecutar las herramientas.
Un kit verificado queda disponible en la caché local para trabajar sin conexión.

La reconstrucción puede tardar varios minutos y comprobará el RomFS completo.
Puedes cancelar la descarga o la compilación. El candidato pasa las pruebas del
ejecutable y del cargador antes de activarse. Un fallo conserva el runtime
anterior; los respaldos y el diario permiten recuperar una sustitución
interrumpida. **Verificar / reconstruir juego** también permite reparar el
runtime de la misma versión. La preparación de shaders se exige después de
cambiar el runtime, aunque la casilla estuviera desactivada.

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
