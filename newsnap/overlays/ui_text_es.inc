// The in-game menu in Spanish (MENU-04), every string of text_en (ui_text.c) and NewSnap's own (snap_menu_adapt.py).
// Included by ui_text.c in place of the keyboard-only Spanish row.
static const char *const text_es[UI_TEXT_COUNT] = {
    SWKBD("Introducir texto", "Introduce un nombre", "Caballo", "Aceptar", "Cancelar", "Mando: A = Aceptar, B = Cancelar"),

    [UI_MENU_TITLE] = "Ajustes",
    [UI_MENU_TAB_SCREEN] = "Pantalla", [UI_MENU_TAB_GAME] = "Juego", [UI_MENU_TAB_MODS] = "Mods", [UI_MENU_TAB_SOUND] = "Sonido",
    [UI_MENU_TAB_CONTROLS] = "Controles", [UI_MENU_TAB_MENU] = "Menú", [UI_MENU_TAB_ADVANCED] = "Avanzado",
    [UI_MENU_CONTINUE] = "Continuar", [UI_MENU_QUIT] = "Salir del juego",
    [UI_MENU_ON] = "Activado", [UI_MENU_OFF] = "Desactivado", [UI_MENU_AUTO] = "Automático",
    [UI_MENU_DEFAULT_MARK] = "predeterminado",
    [UI_MENU_AFTER_RESTART] = "tras reiniciar", [UI_MENU_SET_BY_ENV] = "fijado por una variable de entorno",
    [UI_MENU_SAVE_FAILED] = "no se pudieron guardar los ajustes",
    [UI_MENU_VERSION] = "NewSnapRecomp %s, Snap %s",

    [UI_MENU_FULLSCREEN] = "Pantalla completa",
    [UI_MENU_FULLSCREEN_DESC] = "El juego ocupa toda la pantalla; F11 lo alterna.",
    [UI_MENU_WINDOW_SIZE] = "Tamaño de ventana",
    [UI_MENU_WINDOW_SIZE_DESC] = "Tamaño de la ventana del juego fuera de la pantalla completa.",
    [UI_MENU_WINDOW_SIZE_CUSTOM] = "Personalizado",
    [UI_MENU_PRESENT] = "Presentación", [UI_MENU_PRESENT_DESC] = "Cómo llegan a la pantalla los fotogramas terminados.",
    [UI_MENU_PRESENT_MAILBOX] = "Mailbox", [UI_MENU_PRESENT_VSYNC] = "VSync", [UI_MENU_PRESENT_IMMEDIATE] = "Inmediata",
    [UI_MENU_PRESENT_IN_USE] = "en uso: %s",
    [UI_MENU_GPU] = "Tarjeta gráfica", [UI_MENU_GPU_DESC] = "El dispositivo Vulkan que dibuja el juego.",
    [UI_MENU_GPU_AUTO] = "Automática",
    [UI_MENU_PERF_OVERLAY] = "Información de rendimiento",
    [UI_MENU_PERF_OVERLAY_DESC] = "FPS en la esquina superior derecha. «Completa» añade tiempos de fotograma con gráfica, "
                                  "carga de CPU, GPU y memoria, temperaturas y esperas del hilo de render. F10 cambia el modo.",
    [UI_MENU_PERF_OFF] = "Oculta", [UI_MENU_PERF_FPS] = "FPS", [UI_MENU_PERF_FULL] = "Completa",
    [UI_PERF_LINE_FPS] = "%.0f fps",
    [UI_MENU_GRAPHICS] = "Imagen",
    [UI_MENU_OUTPUT_RES] = "Resolución del juego",
    [UI_MENU_OUTPUT_RES_DESC] = "Tamaño al que el juego dibuja su imagen e interfaz. 1280 x 720 es la más ligera, para GPU "
                                "modestas. Por encima de 1920 x 1080 el juego necesita más memoria (unos 240 MB más a "
                                "2560 x 1440, 790 MB a 3840 x 2160) y tiempo de GPU. Se aplica tras reiniciar. «Automática» "
                                "toma el tamaño de la pantalla: hasta 1920 x 1080, y hasta 3840 x 2160 con un escalador activo.",
    [UI_MENU_UPSCALER] = "Escalado a la ventana",
    [UI_MENU_UPSCALER_DESC] = "Cómo se escala la imagen a la ventana. FSR conserva bordes y detalle más nítidos que el "
                              "bilineal, y enfoca la imagen aunque ya quepa en la ventana.",
    [UI_MENU_UPSCALER_FSR] = "AMD FSR 1", [UI_MENU_UPSCALER_BILINEAR] = "Bilineal",
    [UI_MENU_FOV] = "Campo de visión",
    [UI_MENU_FOV_DESC] = "Cuánto del mundo muestra la cámara, en porcentaje del propio del juego (50 grados en vertical al "
                         "jugar). Las cinemáticas conservan el encuadre del juego.",
    [UI_MENU_ANISO] = "Filtrado de texturas",
    [UI_MENU_ANISO_DESC] = "Filtrado anisotrópico: el suelo, los caminos y las paredes vistos en ángulo siguen nítidos a lo "
                           "lejos en vez de emborronarse. Juego: el nivel que pide el juego, como en Switch. Auto: 16x con "
                           "escala 3D de 1440p, el doble del nivel del juego a 2160p y el del juego en los demás casos.",
    [UI_MENU_ANISO_GAME] = "Juego",
    [UI_MENU_ANISO_AUTO] = "Auto",
    [UI_MENU_SHARPNESS] = "Nitidez de FSR",
    [UI_MENU_SHARPNESS_DESC] = "Enfoque tras el escalado FSR; 0 lo desactiva.",
    [UI_MENU_COLOR] = "Color",
    [UI_MENU_COLOR_PRESET] = "Perfil de color",
    [UI_MENU_COLOR_PRESET_DESC] = "Ajusta los cuatro valores de abajo. Vivo: más contraste y saturación y sombras algo más "
                                  "abiertas (pensado para OLED). Claridad: algo más de contraste, saturación y brillo. Mover "
                                  "un valor deja el perfil en Personalizado. El HUD cambia con la imagen; este menú no.",
    [UI_MENU_COLOR_DEFAULT] = "El del juego", [UI_MENU_COLOR_VIVID] = "Vivo (OLED)", [UI_MENU_COLOR_CLARITY] = "Claridad",
    [UI_MENU_COLOR_CUSTOM] = "Personalizado",
    [UI_MENU_COLOR_BRIGHTNESS] = "Brillo", [UI_MENU_COLOR_BRIGHTNESS_DESC] = "Se suma a cada color; 0 lo deja igual.",
    [UI_MENU_COLOR_CONTRAST] = "Contraste",
    [UI_MENU_COLOR_CONTRAST_DESC] = "Aleja los colores del gris medio (más de 100 %) o los acerca; 100 % los deja igual.",
    [UI_MENU_COLOR_SATURATION] = "Saturación",
    [UI_MENU_COLOR_SATURATION_DESC] = "Intensidad del color frente al gris; 100 % la deja igual.",
    [UI_MENU_COLOR_GAMMA] = "Gamma",
    [UI_MENU_COLOR_GAMMA_DESC] = "Por debajo de 1 aclara los tonos oscuros y medios, por encima los oscurece; 1 los deja igual.",
    [UI_MENU_HDR_GROUP] = "HDR",
    [UI_MENU_HDR] = "Salida HDR",
    [UI_MENU_HDR_DESC] = "Brillos intensos en una pantalla HDR. Necesita el HDR activado en Windows («Usar HDR») o un "
                         "compositor Wayland con gestión de color; sin él la imagen sigue en SDR. Se aplica tras reiniciar. "
                         "El perfil de color de arriba es para SDR y no se usa en HDR.",
    [UI_MENU_HDR_PEAK] = "Brillo máximo",
    [UI_MENU_HDR_PEAK_DESC] = "El máximo de tu pantalla en nits; los brillos más intensos se detienen ahí.",
    [UI_MENU_HDR_GAME] = "Brillo del juego",
    [UI_MENU_HDR_GAME_DESC] = "Nits del blanco de la imagen (blanco papel). 203 es la referencia HDR; súbelo en una sala "
                              "luminosa.",
    [UI_MENU_HDR_UI] = "Brillo del HUD y del menú",
    [UI_MENU_HDR_UI_DESC] = "Nits del blanco del HUD y de este menú.",
    [UI_MENU_HDR_HUE] = "Corrección de tono de los brillos",
    [UI_MENU_HDR_HUE_DESC] = "Los colores intensos, como el fuego o las chispas, tienden al blanco como en la imagen SDR del "
                             "juego, igual que la luz que proyectan; 0 los deja totalmente saturados.",
    [UI_MENU_SHADOW_SCALE] = "Resolución de sombras",
    [UI_MENU_SHADOW_SCALE_DESC] = "Dibuja el mapa de sombras del sol tantas veces más grande por lado que el 2048x2048 del "
                                  "juego: bordes de sombra y sombras de hojas más nítidos, a cambio de memoria de vídeo "
                                  "(unos 85 a 130 MiB a 2x, 340 a 520 MiB a 4x). Se aplica en el próximo inicio.",
    [UI_MENU_AO] = "Oclusión ambiental",
    [UI_MENU_AO_DESC] = "Oscurece pliegues, esquinas y el suelo bajo personajes y objetos, donde llega poca luz del "
                        "entorno. Se calcula en pantalla después de iluminar el mundo; el juego no tiene la suya. «Alta» "
                        "cuesta más tiempo de GPU que «Baja». Se aplica al momento.",
    [UI_MENU_AO_OFF] = "Desactivada",
    [UI_MENU_AO_LOW] = "Baja",
    [UI_MENU_AO_HIGH] = "Alta",
    [UI_MENU_UPSCALING] = "Escalador (FSR / DLSS)",
    [UI_MENU_UPSCALING_DESC] = "Un escalador temporal en lugar del antialiasing del juego: bordes más suaves y menos "
                               "parpadeo, y con un modo por debajo de Nativo más FPS. NVIDIA DLSS necesita una GPU NVIDIA RTX "
                               "y nvngx_dlss.dll junto a newsnap.exe; Intel XeSS, una GPU reciente y libxess.dll junto a "
                               "newsnap.exe; AMD FSR funciona en cualquier GPU. «Automático» usa DLSS donde puede y FSR en "
                               "los demás casos. DLSS y XeSS elegidos aquí se aplican tras reiniciar. El HUD no cambia.",
    [UI_MENU_UPSCALING_DESC_OTHER] = "Un escalador temporal en lugar del antialiasing del juego: bordes más suaves y menos "
                                     "parpadeo, y con un modo por debajo de Nativo más FPS. AMD FSR funciona en cualquier "
                                     "GPU; aquí «Automático» es FSR (NVIDIA DLSS e Intel XeSS son solo para Windows). El "
                                     "HUD no cambia.",
    [UI_MENU_UPSCALING_OFF] = "Desactivado", [UI_MENU_UPSCALING_AUTO] = "Automático",
    [UI_MENU_UPSCALING_UNAVAILABLE] = "no disponible aquí",
    [UI_MENU_UPSCALING_UNTIL] = "%s hasta reiniciar",
    [UI_MENU_UPSCALING_QUALITY] = "Escalado de rendimiento",
    [UI_MENU_UPSCALING_QUALITY_DESC] = "Tamaño al que se dibuja la escena 3D antes de que el escalador la lleve a la "
                                       "resolución del juego (se muestra bajo el valor). Nativo la dibuja a tamaño completo, la "
                                       "más nítida (DLAA con DLSS). Calidad, Equilibrado, Rendimiento y Ultra rendimiento la "
                                       "dibujan a cerca del 67, 58, 50 y 33 % para más FPS; Ultra rendimiento es para "
                                       "3840 x 2160. Se aplica tras reiniciar.",
    [UI_MENU_UPSCALING_NATIVE] = "Desactivado (resolución completa)", [UI_MENU_DLSS_QUALITY] = "Calidad", [UI_MENU_DLSS_BALANCED] = "Equilibrado",
    [UI_MENU_DLSS_PERFORMANCE] = "Rendimiento", [UI_MENU_UPSCALING_ULTRA] = "Ultra rendimiento",
    [UI_MENU_UPSCALING_MODE_OFF] = "sin escalador",
    [UI_MENU_AA] = "Antialiasing (SMAA)",
    [UI_MENU_AA_DESC] = "SMAA suaviza los bordes dentados antes de dibujar el HUD. Alto es el predeterminado; Ultra "
                        "encuentra más bordes con algo más de GPU. No se usa mientras funciona un escalador.",
    [UI_SNAP_SMAA_LOW] = "Bajo", [UI_SNAP_SMAA_MEDIUM] = "Medio", [UI_SNAP_SMAA_HIGH] = "Alto",
    [UI_MENU_AA_OFF] = "Desactivado",
    [UI_MENU_AA_BY_UPSCALER] = "el escalador suaviza los bordes",
    [UI_SNAP_RES] = "Resolución interna del juego",
    [UI_SNAP_RES_DESC] = "Resolución a la que se dibuja la escena 3D. 100 % es el 1920 x 1080 propio del juego: baja para "
                         "una imagen más ligera, sube (supersampling) para una más nítida que cuesta tiempo de GPU. «Según "
                         "la pantalla» iguala la altura de la pantalla o la ventana. Funciona junto con el antialiasing. Se "
                         "aplica tras reiniciar.",
    [UI_SNAP_RES_UPSCALER] = "por encima del 100 %: pon el escalado de rendimiento en Desactivado",
    [UI_SNAP_FG] = "Generación de fotogramas",
    [UI_SNAP_FG_DESC] = "Generación de fotogramas AMD FSR: un fotograma generado entre cada dos reales. La interfaz queda "
                        "fuera de la interpolación. Se pausa sola mientras el juego va más rápido que la mitad del refresco "
                        "del monitor. La información de rendimiento muestra los FPS reales y los generados. Se aplica tras "
                        "reiniciar.",
    [UI_SNAP_FG_NEEDS] = "necesita AMD FSR 3.1 o FSR 4 como escalador",
    [UI_SNAP_HDPH] = "Miniaturas de fotos en HD",
    [UI_SNAP_HDPH_DESC] = "La vista previa tras una foto y las fotos de las carpetas y la selección usan la foto de "
                          "1080 x 720 en vez de la miniatura de 360 x 240 del juego. Las fotos guardadas y la puntuación no "
                          "cambian.",
    [UI_SNAP_SHADOW] = "Resolución de sombras",
    [UI_SNAP_SHADOW_DESC] = "Amplía todos los mapas de sombras del juego. Auto sigue a la resolución 3D: 2x a 1080p, 3x a "
                            "125-150 %, 4x desde 200 %. Las sombras pintadas en el escenario no cambian. Se aplica tras "
                            "reiniciar.",
    [UI_SNAP_TEXPACK] = "Pack de texturas HD",
    [UI_SNAP_TEXPACK_DESC] = "Usa las texturas HD de la carpeta texpack junto al juego, hechas en este PC a partir de tu "
                             "propio juego. Se aplica tras reiniciar.",
    [UI_SNAP_TEXPACK_NONE] = "no hay pack en la carpeta texpack",
    [UI_SNAP_HDSH] = "Modo Sombras HD (experimental)",
    [UI_SNAP_HDSH_DESC] = "Las sombras de plantas, rocas y escenario están pintadas en los mapas de luz de cada nivel. "
                          "Activado: cada mapa de luz se guarda la primera vez que se carga y, al cerrar el juego, el "
                          "launcher los amplía en este PC; los HD se usan la próxima vez que se carga el nivel. Las "
                          "sombras en tiempo real también van a su mapa más grande (desactivado, siguen a la resolución "
                          "interna). Se aplica tras reiniciar.",
    [UI_SNAP_TAB] = "Mejoras",
    [UI_SNAP_ENH] = "Mejoras de NewSnap (no cambian la lógica del juego)",
    [UI_SNAP_ASPECT] = "Relación de aspecto",
    [UI_SNAP_ASPECT_DESC] = "Mantener 16:9 añade bandas en pantallas más anchas; Estirar llena la ventana; Ultrawide amplía "
                            "la vista 3D a la ventana con las proporciones del juego, deja la interfaz en el centro y hace las "
                            "fotos con la vista 16:9 de siempre (experimental).",
    [UI_SNAP_TAB_SYS] = "Sistema",
    [UI_SNAP_SYS_CONT] = "Volver al juego",
    [UI_SNAP_SYS_CONT_DESC] = "Cierra este menú y sigue jugando.",
    [UI_SNAP_SYS_RESTART] = "Reiniciar el juego",
    [UI_SNAP_SYS_RESTART_DESC] = "Cierra el juego y lo abre de nuevo, para los ajustes que se aplican tras reiniciar. Se "
                                 "pierde el progreso desde la última vez que guardaste.",
    [UI_SNAP_SYS_QUIT] = "Salir al escritorio",
    [UI_SNAP_SYS_QUIT_DESC] = "Cierra el juego. Se pierde el progreso desde la última vez que guardaste; el juego guarda "
                              "solo después de cada expedición.",
    [UI_MENU_OUTPUT_RES_AUTO] = "Automática",
    [UI_MENU_OUTPUT_RES_NEXT] = ", %s tras reiniciar",

    [UI_MENU_FPS_LIMIT] = "Límite de FPS",
    [UI_MENU_FPS_LIMIT_DESC] = "Límite de fotogramas: 30, 60 (predeterminado), 90, 120 o 144 FPS, o VRR (justo por debajo "
                               "del refresco del monitor). Las escenas nativas más lentas conservan su ritmo. Se aplica al "
                               "momento; los FPS logrados dependen de la GPU y del modo de pantalla.",
    [UI_MENU_FPS_30] = "30 FPS", [UI_MENU_FPS_60] = "60 FPS",
    [UI_MENU_REALTIME] = "Velocidad del juego según el reloj",
    [UI_MENU_REALTIME_DESC] = "Avanza el juego según el tiempo real, para que un fotograma lento no lo ralentice.",
    [UI_MENU_CLOTH_REALTIME] = "Telas según el reloj",
    [UI_MENU_CLOTH_REALTIME_DESC] = "Avanza también telas y pelo según el tiempo real.",
    [UI_MENU_HIGHFPS_FIX] = "Correcciones para muchos FPS",
    [UI_MENU_HIGHFPS_FIX_DESC] = "Corrige físicas que fallan por encima de 30 FPS y objetos que quedan transparentes o "
                                 "invisibles por encima de 60.",
    [UI_MENU_GAME_LANG] = "Idioma del juego", [UI_MENU_GAME_LANG_DESC] = "Idioma de los textos y las voces del juego.",
    [UI_MENU_GAME_LANG_AUTO] = "Automático",
    [UI_MENU_OPERATION_MODE] = "Modo de consola",
    [UI_MENU_OPERATION_MODE_DESC] = "Si el juego cree que está en el dock (TV) o en modo portátil.",
    [UI_MENU_MODE_DOCKED] = "TV (dock)", [UI_MENU_MODE_HANDHELD] = "Portátil",
    [UI_MENU_HUD] = "HUD",
    [UI_MENU_HUD_DESC] = "Desactivado, no se dibuja el HUD del juego al jugar; los menús siguen. F12 lo alterna.",
    [UI_MENU_ASSUME_FOCUS] = "Seguir sin foco",
    [UI_MENU_ASSUME_FOCUS_DESC] = "Activado (predeterminado), el juego sigue mientras estás en otra ventana y el teclado no "
                                  "actúa hasta que la ventana vuelva al frente. Desactivado, se pausa cuando su ventana "
                                  "pierde el foco, como en Switch al pulsar Home; una carga interrumpida así puede quedarse "
                                  "parada.",

    [UI_MENU_MODS_INSTALLED] = "Mods instalados",
    [UI_MENU_MODS_NONE] = "Aún no hay mods. Descomprime un mod en la carpeta mods, una carpeta por mod con su carpeta romfs "
                          "dentro, y reinicia el juego.",
    [UI_MENU_MODS_OPEN] = "Abrir la carpeta de mods",
    [UI_MENU_MODS_OPEN_DESC] = "Muestra la carpeta de la que el juego carga los mods. Se crea si no existe.",
    [UI_MENU_MODS_ROW_DESC] = "Archivos del juego que reemplaza: %u. Archivos nuevos que añade: %u.",
    [UI_MENU_MODS_OVERRIDDEN] = "%u de sus archivos vienen de %s, que está más arriba en la lista.",
    [UI_MENU_MODS_MOVE_HINT] = "El botón superior o Ctrl+Arriba lo sube, el botón izquierdo o Ctrl+Abajo lo baja. Cuando dos "
                               "mods cambian el mismo archivo, gana el de más arriba. Los cambios se aplican tras reiniciar.",
    [UI_MENU_MODS_EMPTY] = "Esta carpeta no tiene archivos romfs, exefs ni cheats.",
    [UI_MENU_MODS_SUBSDK] = "Este mod trae su propio código del juego (un plugin subsdk o un main reemplazado). El port no "
                            "puede cargar módulos de código, así que el mod entero queda desactivado.",
    [UI_MENU_MODS_EXEFS_LATER] = "Este mod parchea el código del juego (exefs). El juego integra los parches en el próximo "
                                 "inicio (una reconstrucción de unos minutos); hasta entonces el mod entero queda desactivado.",
    [UI_MENU_MODS_CHEATS] = "Trucos: %d.",
    [UI_MENU_MODS_CHEATS_FILE] = "Los trucos de esta versión del juego se leen al iniciar desde cheats\\%s en este mod.",
    [UI_MENU_MODS_BAD_NAME] = "El nombre de la carpeta contiene |, que la lista de mods usa entre nombres. Renombra la "
                              "carpeta.",
    [UI_MENU_MODS_OTHER_VERSION] = "%u de sus archivos son para otra versión del juego y se omiten. Busca una versión de "
                                   "este mod hecha para tu versión del juego.",
    [UI_MENU_MODS_UNUSED] = "sin usar",

    [UI_MENU_VOLUME] = "Volumen", [UI_MENU_VOLUME_DESC] = "Volumen general del juego.",

    [UI_MENU_MOTION] = "Control por movimiento", [UI_MENU_MOTION_DESC] = "Apuntar con el giroscopio del mando.",
    [UI_MENU_RUMBLE_STRENGTH] = "Intensidad de vibración",
    [UI_MENU_RUMBLE_STRENGTH_DESC] = "Con cuánta fuerza vibra el mando.",
    [UI_MENU_RUMBLE_CURVE] = "Curva de vibración",
    [UI_MENU_RUMBLE_CURVE_DESC] = "Valores más bajos refuerzan las vibraciones suaves.",
    [UI_MENU_RUMBLE_TRIGGERS] = "Vibración de gatillos (Xbox)",
    [UI_MENU_RUMBLE_TRIGGERS_DESC] = "Hace vibrar también los gatillos de un mando de Xbox.",
    [UI_MENU_PAD_LAYOUT] = "Distribución de botones",
    [UI_MENU_PAD_LAYOUT_DESC] = "Qué botón es A. Nintendo: el de la derecha, como en Switch. Xbox: el de abajo, como en un "
                                "mando de Xbox. PlayStation: el de abajo (cruz) y el resto por posición, para el mod de "
                                "botones de PlayStation. «Automática» elige Nintendo para mandos con rótulos de Nintendo, "
                                "PlayStation para mandos de PlayStation y Xbox para los demás. Qué mando muestran los avisos "
                                "del juego se elige en Avisos de botones.",
    [UI_MENU_PAD_LAYOUT_AUTO] = "Automática", [UI_MENU_PAD_LAYOUT_NINTENDO] = "Nintendo (A a la derecha)",
    [UI_MENU_PAD_LAYOUT_XBOX] = "Xbox (A abajo)", [UI_MENU_PAD_LAYOUT_PLAYSTATION] = "PlayStation (A abajo)",
    [UI_MENU_PAD_LAYOUT_IN_USE] = "en uso: %s",
    [UI_MENU_PROMPTS] = "Avisos de botones",
    [UI_MENU_PROMPTS_DESC] = "Qué botones de mando muestran los avisos del juego. «Automático» sigue al mando en uso. "
                             "Nintendo: los del juego. Xbox y PlayStation: mods de botones dibujados para cada distribución. "
                             "El juego lee sus avisos al iniciar, así que cambian tras reiniciar.",
    [UI_MENU_PROMPTS_AUTO] = "Automático", [UI_MENU_PROMPTS_NINTENDO] = "Nintendo", [UI_MENU_PROMPTS_XBOX] = "Xbox",
    [UI_MENU_PROMPTS_PLAYSTATION] = "PlayStation",
    [UI_MENU_PROMPTS_MISSING] = "faltan archivos de avisos: vuelve a ejecutar la instalación",
    [UI_MENU_PROMPTS_FAILED] = "archivos de avisos dañados: vuelve a ejecutar la instalación",
    [UI_MENU_PROMPTS_RESTART] = "los avisos cambian tras reiniciar",
    [UI_MENU_PROMPTS_OFF_SHAPE] = "desactivado con una resolución del juego que no es 16:9",
    [UI_MENU_PROMPTS_OFF_MODS] = "desactivado: un mod de RomFS reemplaza sus archivos",
    [UI_MENU_PROMPTS_OFF_PATCHES] = "desactivado mientras AC_ROMFS_PATCHES esté definido",
    [UI_MENU_RESTART] = "Reiniciar ahora",
    [UI_MENU_RESTART_DESC] = "Cierra el juego y lo abre de nuevo con los nuevos avisos. Se pierde el progreso desde la "
                             "última vez que guardaste.",
    [UI_MENU_RESTART_CONFIRM] = "¿Reiniciar el juego ahora? Se pierde el progreso desde la última vez que guardaste.",
    [UI_MENU_RESTART_YES] = "Reiniciar",
    [UI_MENU_RESTART_SAVING] = "El juego está guardando: podrás reiniciar en un momento.",
    [UI_MENU_LSTICK_DEADZONE] = "Zona muerta del stick izquierdo", [UI_MENU_RSTICK_DEADZONE] = "Zona muerta del stick derecho",
    [UI_MENU_STICK_DEADZONE_DESC] = "Cuánto se mueve un stick antes de que el juego lo note. Súbela si el personaje o la "
                                    "cámara se mueven solos: suelta el stick, mira «stick ahora» y pon la zona muerta unos "
                                    "puntos por encima.",
    [UI_MENU_STICK_DEADZONE_NOW] = "stick ahora: %.0f %%",
    [UI_MENU_MOUSE_SENS] = "Sensibilidad del ratón",
    [UI_MENU_MOUSE_SENS_DESC] = "Qué tan rápido gira la cámara con el ratón.",
    [UI_MENU_WALK_KEY] = "Tecla de caminar",
    [UI_MENU_WALK_KEY_DESC] = "Al mantenerla, los sticks del teclado se inclinan solo en parte, para caminar en vez de "
                              "correr. La escala de caminar fija cuánto. No afecta al mando ni al ratón.",
    [UI_MENU_WALK_KEY_TAKEN] = "también %s",
    [UI_MENU_WALK_SCALE] = "Escala de caminar",
    [UI_MENU_WALK_SCALE_DESC] = "Inclinación de los sticks del teclado con la tecla de caminar. La mitad es caminar, el "
                                "máximo es correr.",
    [UI_MENU_STICK_SENS] = "Velocidad de cámara con stick",
    [UI_MENU_STICK_SENS_DESC] = "Multiplica la velocidad de cámara del stick derecho del juego, máxima incluida, en cada una "
                                "de sus cinco sensibilidades. El ratón tiene su propio ajuste.",

    [UI_BINDS_HELP] = "Elige una casilla y pulsa A o Intro, luego la tecla, botón del ratón o botón del mando. Supr o X "
                      "vacía una casilla. Una tecla en uso se mueve aquí; un botón del mando se intercambia con el que "
                      "reemplaza.",
    [UI_BINDS_COL_KEY1] = "Tecla 1", [UI_BINDS_COL_KEY2] = "Tecla 2", [UI_BINDS_COL_PAD] = "Mando",
    [UI_BINDS_GROUP_BUTTONS] = "Botones", [UI_BINDS_GROUP_MOVE] = "Movimiento", [UI_BINDS_GROUP_CAMERA] = "Cámara",
    [UI_BINDS_PRESS_KEY] = "Pulsa una tecla o botón del ratón para %s",
    [UI_BINDS_PRESS_PAD] = "Pulsa un botón del mando para %s",
    [UI_BINDS_CANCEL_HINT] = "Esc cancela, o espera %d s",
    [UI_BINDS_TAKEN] = "%s se quitó de %s", [UI_BINDS_SWAPPED] = "%s intercambiado con %s",
    [UI_BINDS_RESET] = "Restablecer todos los botones",
    [UI_BINDS_RESET_DESC] = "Vuelve a las teclas y botones predeterminados. La distribución de arriba vuelve a aplicarse: los "
                            "botones del mando reasignados se quedan donde los pusiste hasta este restablecimiento.",
    [UI_BIND_A] = "A", [UI_BIND_B] = "B", [UI_BIND_X] = "X", [UI_BIND_Y] = "Y",
    [UI_BIND_LCLICK] = "Pulsar stick izquierdo", [UI_BIND_RCLICK] = "Pulsar stick derecho", [UI_BIND_L] = "L",
    [UI_BIND_R] = "R", [UI_BIND_ZL] = "ZL", [UI_BIND_ZR] = "ZR", [UI_BIND_PLUS] = "Más (+)", [UI_BIND_MINUS] = "Menos (-)",
    [UI_BIND_LEFT] = "Cruceta izquierda", [UI_BIND_UP] = "Cruceta arriba", [UI_BIND_RIGHT] = "Cruceta derecha",
    [UI_BIND_DOWN] = "Cruceta abajo",
    [UI_BIND_LSTICK_LEFT] = "Mover a la izquierda", [UI_BIND_LSTICK_UP] = "Mover adelante",
    [UI_BIND_LSTICK_RIGHT] = "Mover a la derecha", [UI_BIND_LSTICK_DOWN] = "Mover atrás",
    [UI_BIND_RSTICK_LEFT] = "Cámara a la izquierda", [UI_BIND_RSTICK_UP] = "Cámara arriba",
    [UI_BIND_RSTICK_RIGHT] = "Cámara a la derecha", [UI_BIND_RSTICK_DOWN] = "Cámara abajo",
    [UI_BIND_DESC_A] = "Interactuar, recoger, hablar.", [UI_BIND_DESC_B] = "Correr, cancelar, volver.",
    [UI_BIND_DESC_X] = "Saltar.", [UI_BIND_DESC_Y] = "Atacar.", [UI_BIND_DESC_LCLICK] = "Agacharse.",
    [UI_BIND_DESC_RCLICK] = "Vista en primera persona.", [UI_BIND_DESC_L] = "Habilidades.",
    [UI_BIND_DESC_R] = "Lanzar.", [UI_BIND_DESC_ZL] = "Escudo, fijar.", [UI_BIND_DESC_ZR] = "Arco.",
    [UI_BIND_DESC_PLUS] = "Menú, inventario.", [UI_BIND_DESC_MINUS] = "Mapa.",
    [UI_BIND_DESC_DPAD] = "Selección rápida.",
    [UI_BIND_DESC_MOVE] = "Mueve como el stick izquierdo. El stick izquierdo del mando funciona siempre también.",
    [UI_BIND_DESC_CAMERA] = "Gira la cámara como el stick derecho. El ratón y el stick derecho del mando funcionan siempre "
                            "también.",
    [UI_KEY_SPACE] = "Espacio", [UI_KEY_TAB] = "Tab", [UI_KEY_LSHIFT] = "Mayús izq.", [UI_KEY_LCTRL] = "Ctrl izq.",
    [UI_KEY_UP] = "Flecha arriba", [UI_KEY_DOWN] = "Flecha abajo", [UI_KEY_LEFT] = "Flecha izquierda",
    [UI_KEY_RIGHT] = "Flecha derecha",
    [UI_KEY_MOUSE_L] = "Clic izquierdo", [UI_KEY_MOUSE_R] = "Clic derecho", [UI_KEY_MOUSE_M] = "Clic central",
    [UI_KEY_MOUSE_X1] = "Ratón 4", [UI_KEY_MOUSE_X2] = "Ratón 5",
    [UI_KEY_ENTER] = "Intro", [UI_KEY_BACKSPACE] = "Retroceso", [UI_KEY_RSHIFT] = "Mayús der.",
    [UI_KEY_RCTRL] = "Ctrl der.", [UI_KEY_LALT] = "Alt", [UI_KEY_CAPSLOCK] = "Bloq Mayús", [UI_KEY_INSERT] = "Insert",
    [UI_KEY_DELETE] = "Supr", [UI_KEY_HOME] = "Inicio", [UI_KEY_END] = "Fin", [UI_KEY_PAGEUP] = "Re Pág",
    [UI_KEY_PAGEDOWN] = "Av Pág", [UI_KEY_NUM_FMT] = "Num %s",
    [UI_PAD_SOUTH] = "Botón inferior", [UI_PAD_EAST] = "Botón derecho", [UI_PAD_WEST] = "Botón izquierdo",
    [UI_PAD_NORTH] = "Botón superior", [UI_PAD_LSTICK] = "Stick izquierdo", [UI_PAD_RSTICK] = "Stick derecho",
    [UI_PAD_L] = "Botón superior izquierdo", [UI_PAD_R] = "Botón superior derecho", [UI_PAD_START] = "Start",
    [UI_PAD_BACK] = "Back",
    [UI_PAD_DPAD_LEFT] = "Cruceta izquierda", [UI_PAD_DPAD_UP] = "Cruceta arriba", [UI_PAD_DPAD_RIGHT] = "Cruceta derecha",
    [UI_PAD_DPAD_DOWN] = "Cruceta abajo", [UI_PAD_ZL] = "Gatillo izquierdo", [UI_PAD_ZR] = "Gatillo derecho",
    [UI_PAD_LPADDLE1] = "Botón trasero izquierdo", [UI_PAD_RPADDLE1] = "Botón trasero derecho",
    [UI_PAD_LPADDLE2] = "Botón trasero izquierdo 2", [UI_PAD_RPADDLE2] = "Botón trasero derecho 2",
    [UI_PAD_CROSS] = "Cruz", [UI_PAD_CIRCLE] = "Círculo", [UI_PAD_SQUARE] = "Cuadrado", [UI_PAD_TRIANGLE] = "Triángulo",

    [UI_MENU_MENU_LANG] = "Idioma del menú", [UI_MENU_MENU_LANG_DESC] = "Idioma de este menú y de la información en pantalla.",
    [UI_MENU_MENU_LANG_AUTO] = "Automático (de Windows)",

    [UI_MENU_ADV_WARNING] = "Estos ajustes son para pruebas y para resolver problemas. Cámbialos solo si sabes por qué.",
    [UI_MENU_GROUP_SCHED] = "Planificación", [UI_MENU_GROUP_SHADERS] = "Shaders y pipelines",
    [UI_MENU_GROUP_TEXMEM] = "Texturas y memoria", [UI_MENU_GROUP_FIXES] = "Correcciones de render",
    [UI_MENU_GROUP_VULKAN] = "Vulkan", [UI_MENU_GROUP_DIAG] = "Diagnóstico",
    [UI_MENU_ASYNC_PREEMPT] = "Desalojo de núcleos virtuales",
    [UI_MENU_ASYNC_PREEMPT_DESC] = "Permite que un hilo del juego interrumpa a otro en el mismo núcleo virtual.",
    [UI_MENU_PREEMPT_OFF] = "Desactivado", [UI_MENU_PREEMPT_ON] = "Activado", [UI_MENU_PREEMPT_INHERIT] = "Solo herencia",
    [UI_MENU_REPLAY_ASYNC] = "Preparar fotogramas en su propio hilo",
    [UI_MENU_REPLAY_ASYNC_DESC] = "Prepara los fotogramas para la GPU en un hilo aparte en vez del hilo del juego. Añade "
                                  "hasta un fotograma de latencia.",
    [UI_MENU_TIMER_1MS] = "Temporizador de Windows de 1 ms",
    [UI_MENU_TIMER_1MS_DESC] = "Sube la resolución del temporizador del sistema a 1 ms para un ritmo de fotogramas más estable.",
    [UI_MENU_PIPE_WAIT] = "Tratamiento de dibujos en espera",
    [UI_MENU_PIPE_WAIT_DESC] = "Predeterminado mantiene la planificación actual con un trabajador reservado para los dibujos "
                               "en espera; Antiguo (dibujo) usa la planificación anterior.",
    [UI_MENU_PIPE_WAIT_DEFAULT] = "Predeterminado", [UI_MENU_PIPE_WAIT_DRAW] = "Antiguo (dibujo)",
    [UI_MENU_PIPE_SKIP] = "Dibujos omitidos mientras se crea un pipeline",
    [UI_MENU_PIPE_SKIP_DESC] = "Qué dibujos se descartan en vez de esperar a su pipeline.",
    [UI_MENU_PIPE_SKIP_STRICT] = "Estricto", [UI_MENU_PIPE_SKIP_ANY] = "Cualquiera",
    [UI_MENU_PIPE_SKIP_FULLSCREEN] = "Pasadas de pantalla completa",
    [UI_MENU_LIB_PREBUILD] = "Precompilar bibliotecas de etapas",
    [UI_MENU_LIB_PREBUILD_DESC] = "Compila por adelantado y en segundo plano las bibliotecas de etapas de shaders.",
    [UI_MENU_LIB_PREBUILD_THREADS] = "Hilos de precompilación de bibliotecas",
    [UI_MENU_LIB_PREBUILD_THREADS_DESC] = "Hilos usados para precompilar; «Automático» elige un número según tu CPU.",
    [UI_MENU_PIPE_PREBUILD] = "Precompilar pipelines",
    [UI_MENU_PIPE_PREBUILD_DESC] = "Compila por adelantado los pipelines conocidos.",
    [UI_MENU_PREWARM_XLATE] = "Precalentar el traductor",
    [UI_MENU_PREWARM_XLATE_DESC] = "Hilos que traducen los shaders conocidos al iniciar; «Automático» usa la mitad de los "
                                   "hilos de la CPU, como mucho 16.",
    [UI_MENU_GPL] = "Biblioteca de pipelines gráficos",
    [UI_MENU_GPL_DESC] = "Usa la extensión de bibliotecas de pipelines de Vulkan; desactívala si tu controlador falla con ella.",
    [UI_MENU_ASTC] = "Decodificación de texturas ASTC",
    [UI_MENU_ASTC_DESC] = "Dónde se decodifican las texturas comprimidas ASTC.",
    [UI_MENU_ASTC_AUTO] = "Automática", [UI_MENU_ASTC_GPU] = "Shader de GPU", [UI_MENU_ASTC_NATIVE] = "Nativa",
    [UI_MENU_ASTC_CPU] = "CPU",
    [UI_MENU_MEMORY] = "Modo de memoria de GPU",
    [UI_MENU_MEMORY_DESC] = "Cómo se comparte la memoria del juego con la GPU.",
    [UI_MENU_MEMORY_AUTO] = "Automático", [UI_MENU_MEMORY_IMPORT] = "Importar", [UI_MENU_MEMORY_MIRROR] = "Espejo",
    [UI_MENU_MEMORY_VERIFY] = "Verificar",
    [UI_MENU_TEX_ALIAS] = "Alias de texturas",
    [UI_MENU_TEX_ALIAS_DESC] = "Una textura nueva creada sobre la memoria de otra viva empieza con ese contenido en vez de "
                               "vacía.",
    [UI_MENU_TEX_VRAM_PRESSURE] = "Límite de memoria de texturas",
    [UI_MENU_TEX_VRAM_PRESSURE_DESC] = "Porcentaje de memoria de vídeo a partir del cual se descartan las texturas que el "
                                       "juego liberó (vuelven del almacenamiento cuando se usan). 0 las conserva.",
    [UI_MENU_ASTC_BC] = "Comprimir ASTC a BC",
    [UI_MENU_ASTC_BC_DESC] = "Con el decodificador de GPU: recodifica las texturas ASTC decodificadas a BC1 si son opacas y "
                             "a BC3 si no, entre un cuarto y un octavo de la memoria de vídeo. Para GPU de 4 GB o menos; las "
                             "texturas se ven algo más en bloques.",
    [UI_MENU_LOD_GUARD] = "Protección de LOD",
    [UI_MENU_LOD_GUARD_DESC] = "Evita que los objetos parpadeen en un sitio equivocado o que el fondo lejano quede plano un "
                               "fotograma, esperando a que el juego termine de reescribir los niveles de detalle antes de "
                               "que la GPU los lea.",
    [UI_MENU_FIX_C0] = "Corrección del búfer de constantes",
    [UI_MENU_FIX_C0_DESC] = "Rellena el banco de constantes c0 reservado del controlador (tamaños de almacenamiento, tamaño "
                            "de despacho, tamaño de punto, instancia base) en vez de leer ceros.",
    [UI_MENU_FIX_ZERO] = "Poner a cero la memoria de GPU nueva",
    [UI_MENU_FIX_ZERO_DESC] = "Los grupos de memoria de GPU nuevos empiezan a cero, como la memoria de Switch.",
    [UI_MENU_BIND_SKIP] = "Omitir enlaces repetidos",
    [UI_MENU_BIND_SKIP_DESC] = "Optimización: omite los enlaces que no cambiaron.",
    [UI_MENU_SHADER_MEMO] = "Memoria de shaders", [UI_MENU_SHADER_MEMO_DESC] = "Optimización: recuerda las búsquedas de shaders.",
    [UI_MENU_PIPE_MEMO] = "Memoria de pipelines",
    [UI_MENU_PIPE_MEMO_DESC] = "Optimización: reutiliza el pipeline del dibujo anterior cuando su estado se repite.",
    [UI_MENU_TEX_MEMO] = "Memoria de enlaces de texturas",
    [UI_MENU_TEX_MEMO_DESC] = "Optimización: recuerda los descriptores de texturas entre dibujos.",
    [UI_MENU_DESC_TEMPLATE] = "Plantillas de descriptores",
    [UI_MENU_DESC_TEMPLATE_DESC] = "Optimización: actualiza los descriptores en bloque.",
    [UI_MENU_PUSH_SKIP] = "Omitir push constants repetidas",
    [UI_MENU_PUSH_SKIP_DESC] = "Optimización: omite las push constants que no cambiaron.",
    [UI_MENU_SPLIT_DRAWS] = "Envío anticipado a la GPU",
    [UI_MENU_SPLIT_DRAWS_DESC] = "Envía el trabajo de GPU por partes cada N dibujos entre pasadas para que la GPU empiece "
                                 "antes; 0 lo desactiva.",
    [UI_MENU_VK_VALIDATION] = "Capa de validación",
    [UI_MENU_VK_VALIDATION_DESC] = "Comprueba cada llamada de Vulkan y ralentiza mucho el juego.",
    [UI_MENU_VK_VALIDATION_MISSING] = "La capa de validación no está instalada.",
    [UI_MENU_VK_DYN_VERTEX] = "Estado de vértices dinámico",
    [UI_MENU_VK_DYN_VERTEX_DESC] = "Fuerza la entrada de vértices dinámica activada o desactivada; lo predeterminado depende "
                                   "de la GPU.",
    [UI_MENU_VK_DYN_A2C] = "Alpha to coverage dinámico",
    [UI_MENU_VK_DYN_A2C_DESC] = "Fuerza el alpha to coverage dinámico activado o desactivado. Predeterminado: desactivado en "
                                "el controlador de AMD para RDNA 2 y anteriores, que con él dibuja personajes en negro; "
                                "activado en los demás.",
    [UI_MENU_VK_SUBGROUP_PIN] = "Fijar el tamaño de subgrupo",
    [UI_MENU_VK_SUBGROUP_PIN_DESC] = "Fija el tamaño de subgrupo de los shaders.",
    [UI_MENU_TRACE] = "Registro de rendimiento", [UI_MENU_TRACE_DESC] = "Escribe los tiempos de fotograma en un archivo.",
    [UI_MENU_FLIGHT] = "Grabadora de vuelo",
    [UI_MENU_FLIGHT_DESC] = "Guarda un historial corto y lo escribe cuando un fotograma se congela.",
    [UI_MENU_FLIGHT_SPIKE_MS] = "Umbral de congelación (ms)",
    [UI_MENU_FLIGHT_SPIKE_MS_DESC] = "Tiempo de fotograma que cuenta como congelación.",
    [UI_MENU_INPUT_RECORD] = "Grabar la entrada",
    [UI_MENU_INPUT_RECORD_DESC] = "Escribe tus pulsaciones en un archivo para informar de errores.",
    [UI_MENU_OPEN_LOG] = "Abrir la carpeta de registros", [UI_MENU_OPEN_LOG_DESC] = "Muestra la carpeta con los registros.",
    [UI_MENU_COPY_INFO] = "Copiar información del sistema",
    [UI_MENU_COPY_INFO_DESC] = "Copia al portapapeles la GPU, el controlador, la CPU, la RAM y los ajustes cambiados.",
    [UI_MENU_COPY_INFO_DONE] = "Copiado", [UI_MENU_ACTION_FAILED] = "no funcionó",
    [UI_MENU_RESET] = "Restablecer todos los ajustes", [UI_MENU_RESET_DESC] = "Se aplica a todas las pestañas.",
    [UI_MENU_RESET_CONFIRM] = "¿Restablecer todos los ajustes a sus valores predeterminados?",
    [UI_MENU_RESET_YES] = "Restablecer",
    [UI_MENU_RESET_NO] = "Cancelar",

    [UI_MENU_OV_FPS] = "%.0f FPS", [UI_MENU_OV_FRAME_MS] = "%.1f ms", [UI_MENU_OV_GAME_PCT] = "juego %.0f%%",
    [UI_MENU_OV_MAX_MS] = "máx. %.1f ms",
    [UI_MENU_OV_GPU] = "GPU", [UI_MENU_OV_CPU] = "CPU", [UI_MENU_OV_RAM] = "RAM", [UI_MENU_OV_VRAM] = "VRAM",
    [UI_MENU_OV_TEMP] = "Temperatura", [UI_MENU_OV_POWER] = "Consumo", [UI_MENU_OV_CLOCK] = "Frecuencia",
    [UI_MENU_OV_NONE] = "-",
    [UI_MENU_OV_REPLAY] = "Preparación de fotogramas", [UI_MENU_OV_GPU_TIME] = "GPU ocupada por fotograma",
    [UI_MENU_OV_PIPE_WAIT] = "Esperas de pipelines",
    [UI_MENU_OV_SHADER_WAIT] = "Esperas de shaders", [UI_MENU_OV_TEX_UPLOADS] = "Subidas de texturas",
    [UI_MENU_OV_FMT_PCT] = "%.0f%%", [UI_MENU_OV_FMT_TEMP] = "%.0f °C", [UI_MENU_OV_FMT_POWER] = "%.0f W",
    [UI_MENU_OV_FMT_MHZ] = "%.0f MHz", [UI_MENU_OV_FMT_GB] = "%.1f GB", [UI_MENU_OV_FMT_GB_OF] = "/ %.1f GB",
    [UI_MENU_OV_GAME_GB] = "juego %.1f GB", [UI_MENU_OV_FMT_MS] = "%.2f ms", [UI_MENU_OV_PER_FRAME] = "%.1f por fotograma",
    [UI_MENU_OV_WINDOW] = "Ventana", [UI_MENU_OV_OUTPUT] = "Imagen del juego", [UI_MENU_OV_SCENE] = "Escena 3D",
    [UI_MENU_OV_SCALING] = "Escalado", [UI_MENU_OV_LIMIT] = "Límite de FPS", [UI_MENU_OV_PRESENT] = "Presentación",
    [UI_MENU_OV_TEX] = "Compresión de texturas", [UI_MENU_OV_OS] = "Sistema",
    [UI_MENU_OV_FMT_SIZE] = "%ux%u", [UI_MENU_OV_FMT_SCENE] = "%ux%u, %.0f%%",
    [UI_MENU_OV_FMT_FSR] = "AMD FSR 1, nitidez %d%%", [UI_MENU_OV_SCALE_NONE] = "ninguno (1:1)",
    [UI_MENU_OV_SCALE_BILINEAR] = "bilineal",
    [UI_MENU_OV_FMT_AREA] = "promedio de área, nitidez %d%%",
    [UI_MENU_OV_FMT_PRESHARP] = "RCAS antes del HUD, nitidez %d%%",
    [UI_MENU_TAB_CHEATS] = "Trucos",
    [UI_MENU_CHEATS_NONE] = "No hay trucos para esta versión del juego. Los trucos de un mod son un archivo de trucos de "
                            "Atmosphere en su carpeta cheats, con el nombre del build del juego: mods\\<mod>\\cheats\\%s. "
                            "Reinicia el juego para leerlos. Para trucos que cambian el código del juego, el juego se "
                            "reconstruye al iniciar (unos minutos).",
    [UI_MENU_CHEATS_MOD] = "%s: %d trucos",
    [UI_MENU_CHEAT_CODE_DESC] = "Cambia el código del juego. Se activa al momento.",
    [UI_MENU_CHEAT_KEY_DESC] = "Cambia el código del juego mientras mantienes %s. Se activa al momento.",
    [UI_MENU_CHEAT_DATA_DESC] = "Escribe en la memoria del juego en cada fotograma mientras está activado.",
    [UI_MENU_CHEAT_MASTER] = "siempre activado",
    [UI_MENU_CHEAT_MASTER_DESC] = "El código maestro del archivo: siempre está activado.",
    [UI_MENU_CHEAT_RESTORE] = "no hace falta",
    [UI_MENU_CHEAT_RESTORE_DESC] = "Solo vuelve a escribir el código original del juego. Desactivar un truco ya lo hace.",
    [UI_MENU_CHEAT_REBUILD] = "tras la reconstrucción",
    [UI_MENU_CHEAT_REBUILD_DESC] = "Este truco cambia el código del juego y es nuevo o se editó desde que se construyó el "
                                   "juego. El juego lo integra en el próximo inicio (unos minutos), o usa Reconstruir el "
                                   "juego ahora.",
    [UI_MENU_CHEAT_UNSUPPORTED] = "no compatible",
    [UI_MENU_CHEAT_UNSUPPORTED_DESC] = "Este truco no se puede usar con esta versión del juego:",
    [UI_MENU_CHEATS_REBUILD] = "Reconstruir el juego ahora",
    [UI_MENU_CHEATS_REBUILD_DESC] = "Algunos trucos cambian el código del juego y no están integrados: son nuevos o se "
                                    "editaron, o su última reconstrucción falló o se canceló. Cierra el juego; la instalación "
                                    "los integra (unos minutos) y vuelve a abrir el juego. Se pierde el progreso desde la "
                                    "última vez que guardaste.",
    [UI_MENU_MODS_EXEFS_UNSUPPORTED] = "Este mod parchea el código del juego (exefs) de una forma que el port no puede "
                                       "aplicar, así que el mod entero queda desactivado. %s",
    [UI_MENU_MODS_EXEFS_OTHER] = "Sus parches de código (exefs) son para otra versión del juego.",
    [UI_MENU_MODS_EXEFS_ON] = "Parches de código en uso: %d archivos.",
    [UI_MENU_MODS_REPLACES_BUILTIN] = "Parches de código en uso: %d archivos. Reemplazan el parche propio del port %s, que "
                                      "queda desactivado mientras este mod esté activado.",
};
