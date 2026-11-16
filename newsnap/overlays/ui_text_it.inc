// The in-game menu in Italian (MENU-LANG-01), every string of text_es (ui_text_es.inc).
// Included by ui_text.c in place of the keyboard-only Italian row.
static const char *const text_it[UI_TEXT_COUNT] = {
    SWKBD("Inserimento testo", "Inserisci un nome", "Cavallo", "OK", "Annulla", "Controller: A = OK, B = Annulla"),

    [UI_MENU_TITLE] = "Impostazioni",
    [UI_MENU_TAB_SCREEN] = "Schermo", [UI_MENU_TAB_GAME] = "Gioco", [UI_MENU_TAB_MODS] = "Mod", [UI_MENU_TAB_SOUND] = "Audio",
    [UI_MENU_TAB_CONTROLS] = "Comandi", [UI_MENU_TAB_MENU] = "Menu", [UI_MENU_TAB_ADVANCED] = "Avanzate",
    [UI_MENU_CONTINUE] = "Continua", [UI_MENU_QUIT] = "Esci dal gioco",
    [UI_MENU_ON] = "Attivato", [UI_MENU_OFF] = "Disattivato", [UI_MENU_AUTO] = "Automatico",
    [UI_MENU_DEFAULT_MARK] = "predefinito",
    [UI_MENU_AFTER_RESTART] = "dopo il riavvio", [UI_MENU_SET_BY_ENV] = "fissato da una variabile d'ambiente",
    [UI_MENU_SAVE_FAILED] = "impossibile salvare le impostazioni",
    [UI_MENU_VERSION] = "NewSnapRecomp %s, Snap %s",

    [UI_MENU_FULLSCREEN] = "Schermo intero",
    [UI_MENU_FULLSCREEN_DESC] = "Il gioco occupa tutto lo schermo; F11 lo attiva o disattiva.",
    [UI_MENU_WINDOW_SIZE] = "Dimensioni della finestra",
    [UI_MENU_WINDOW_SIZE_DESC] = "Dimensioni della finestra del gioco quando non è a schermo intero.",
    [UI_MENU_WINDOW_SIZE_CUSTOM] = "Personalizzate",
    [UI_MENU_PRESENT] = "Presentazione", [UI_MENU_PRESENT_DESC] = "Come arrivano sullo schermo i fotogrammi completati.",
    [UI_MENU_PRESENT_MAILBOX] = "Mailbox", [UI_MENU_PRESENT_VSYNC] = "VSync", [UI_MENU_PRESENT_IMMEDIATE] = "Immediata",
    [UI_MENU_PRESENT_IN_USE] = "in uso: %s",
    [UI_MENU_GPU] = "Scheda grafica", [UI_MENU_GPU_DESC] = "Il dispositivo Vulkan che disegna il gioco.",
    [UI_MENU_GPU_AUTO] = "Automatica",
    [UI_MENU_PERF_OVERLAY] = "Informazioni sulle prestazioni",
    [UI_MENU_PERF_OVERLAY_DESC] = "FPS nell'angolo in alto a destra. «Completa» aggiunge i tempi dei fotogrammi con grafico, "
                                  "carico di CPU, GPU e memoria, temperature e attese del thread di rendering. F10 cambia la "
                                  "modalità.",
    [UI_MENU_PERF_OFF] = "Nascosta", [UI_MENU_PERF_FPS] = "FPS", [UI_MENU_PERF_FULL] = "Completa",
    [UI_PERF_LINE_FPS] = "%.0f fps",
    [UI_MENU_GRAPHICS] = "Immagine",
    [UI_MENU_OUTPUT_RES] = "Risoluzione del gioco",
    [UI_MENU_OUTPUT_RES_DESC] = "Dimensioni a cui il gioco disegna immagine e interfaccia. 1280 x 720 è la più leggera, per "
                                "GPU modeste. Oltre 1920 x 1080 il gioco richiede più memoria (circa 240 MB in più a "
                                "2560 x 1440, 790 MB a 3840 x 2160) e più tempo di GPU. Si applica dopo il riavvio. "
                                "«Automatica» usa le dimensioni dello schermo: fino a 1920 x 1080, e fino a 3840 x 2160 con "
                                "un upscaler attivo.",
    [UI_MENU_UPSCALER] = "Adattamento alla finestra",
    [UI_MENU_UPSCALER_DESC] = "Come l'immagine viene adattata alla finestra. FSR mantiene bordi e dettagli più nitidi del "
                              "bilineare e rende l'immagine più nitida anche se entra già nella finestra.",
    [UI_MENU_UPSCALER_FSR] = "AMD FSR 1", [UI_MENU_UPSCALER_BILINEAR] = "Bilineare",
    [UI_MENU_FOV] = "Campo visivo",
    [UI_MENU_FOV_DESC] = "Quanta parte del mondo mostra la telecamera, in percentuale di quello del gioco (50 gradi in "
                         "verticale durante il gioco). I filmati mantengono l'inquadratura del gioco.",
    [UI_MENU_ANISO] = "Filtro delle texture",
    [UI_MENU_ANISO_DESC] = "Filtro anisotropico: terreno, sentieri e pareti visti di sbieco restano nitidi in lontananza "
                           "invece di sfocarsi. Gioco: il livello richiesto dal gioco, come su Switch. Auto: 16x con scala "
                           "3D a 1440p, il doppio del livello del gioco a 2160p e quello del gioco negli altri casi.",
    [UI_MENU_ANISO_GAME] = "Gioco",
    [UI_MENU_ANISO_AUTO] = "Auto",
    [UI_MENU_SHARPNESS] = "Nitidezza di FSR",
    [UI_MENU_SHARPNESS_DESC] = "Nitidezza applicata dopo l'upscaling FSR; 0 la disattiva.",
    [UI_MENU_COLOR] = "Colore",
    [UI_MENU_COLOR_PRESET] = "Profilo colore",
    [UI_MENU_COLOR_PRESET_DESC] = "Regola i quattro valori qui sotto. Vivido: più contrasto e saturazione e ombre un po' più "
                                  "aperte (pensato per OLED). Chiarezza: un po' più di contrasto, saturazione e luminosità. "
                                  "Modificare un valore porta il profilo su Personalizzato. L'HUD cambia con l'immagine; "
                                  "questo menu no.",
    [UI_MENU_COLOR_DEFAULT] = "Quello del gioco", [UI_MENU_COLOR_VIVID] = "Vivido (OLED)", [UI_MENU_COLOR_CLARITY] = "Chiarezza",
    [UI_MENU_COLOR_CUSTOM] = "Personalizzato",
    [UI_MENU_COLOR_BRIGHTNESS] = "Luminosità", [UI_MENU_COLOR_BRIGHTNESS_DESC] = "Si somma a ogni colore; 0 lo lascia invariato.",
    [UI_MENU_COLOR_CONTRAST] = "Contrasto",
    [UI_MENU_COLOR_CONTRAST_DESC] = "Allontana i colori dal grigio medio (oltre 100 %) o li avvicina; 100 % li lascia invariati.",
    [UI_MENU_COLOR_SATURATION] = "Saturazione",
    [UI_MENU_COLOR_SATURATION_DESC] = "Intensità del colore rispetto al grigio; 100 % la lascia invariata.",
    [UI_MENU_COLOR_GAMMA] = "Gamma",
    [UI_MENU_COLOR_GAMMA_DESC] = "Sotto 1 schiarisce i toni scuri e medi, sopra li scurisce; 1 li lascia invariati.",
    [UI_MENU_HDR_GROUP] = "HDR",
    [UI_MENU_HDR] = "Uscita HDR",
    [UI_MENU_HDR_DESC] = "Luci intense su uno schermo HDR. Richiede l'HDR attivato in Windows («Usa HDR») o un compositor "
                         "Wayland con gestione del colore; altrimenti l'immagine resta in SDR. Si applica dopo il riavvio. "
                         "Il profilo colore qui sopra è per l'SDR e non viene usato in HDR.",
    [UI_MENU_HDR_PEAK] = "Luminosità massima",
    [UI_MENU_HDR_PEAK_DESC] = "Il massimo del tuo schermo in nit; le luci più intense si fermano lì.",
    [UI_MENU_HDR_GAME] = "Luminosità del gioco",
    [UI_MENU_HDR_GAME_DESC] = "Nit del bianco dell'immagine (bianco carta). 203 è il riferimento HDR; aumentalo in una stanza "
                              "luminosa.",
    [UI_MENU_HDR_UI] = "Luminosità di HUD e menu",
    [UI_MENU_HDR_UI_DESC] = "Nit del bianco dell'HUD e di questo menu.",
    [UI_MENU_HDR_HUE] = "Correzione della tinta delle luci",
    [UI_MENU_HDR_HUE_DESC] = "I colori intensi, come il fuoco o le scintille, tendono al bianco come nell'immagine SDR del "
                             "gioco, così come la luce che proiettano; 0 li lascia del tutto saturi.",
    [UI_MENU_SHADOW_SCALE] = "Risoluzione delle ombre",
    [UI_MENU_SHADOW_SCALE_DESC] = "Disegna la mappa delle ombre del sole tante volte più grande per lato rispetto al "
                                  "2048x2048 del gioco: bordi delle ombre e ombre delle foglie più nitidi, a costo di memoria "
                                  "video (circa 85-130 MiB a 2x, 340-520 MiB a 4x). Si applica al prossimo avvio.",
    [UI_MENU_AO] = "Occlusione ambientale",
    [UI_MENU_AO_DESC] = "Scurisce pieghe, angoli e il terreno sotto personaggi e oggetti, dove arriva poca luce "
                        "dall'ambiente. Si calcola sullo schermo dopo aver illuminato il mondo; il gioco non ne ha una "
                        "propria. «Alta» richiede più tempo di GPU di «Bassa». Si applica subito.",
    [UI_MENU_AO_OFF] = "Disattivata",
    [UI_MENU_AO_LOW] = "Bassa",
    [UI_MENU_AO_HIGH] = "Alta",
    [UI_MENU_UPSCALING] = "Upscaler (FSR / DLSS)",
    [UI_MENU_UPSCALING_DESC] = "Un upscaler temporale al posto dell'antialiasing del gioco: bordi più morbidi e meno "
                               "sfarfallio, e con una modalità inferiore a Nativa più FPS. NVIDIA DLSS richiede una GPU "
                               "NVIDIA RTX e nvngx_dlss.dll accanto a newsnap.exe; Intel XeSS, una GPU recente e libxess.dll "
                               "accanto a newsnap.exe; AMD FSR funziona su qualsiasi GPU. «Automatico» usa DLSS dove può e "
                               "FSR negli altri casi. DLSS e XeSS scelti qui si applicano dopo il riavvio. L'HUD non cambia.",
    [UI_MENU_UPSCALING_DESC_OTHER] = "Un upscaler temporale al posto dell'antialiasing del gioco: bordi più morbidi e meno "
                                     "sfarfallio, e con una modalità inferiore a Nativa più FPS. AMD FSR funziona su "
                                     "qualsiasi GPU; qui «Automatico» è FSR (NVIDIA DLSS e Intel XeSS sono solo per "
                                     "Windows). L'HUD non cambia.",
    [UI_MENU_UPSCALING_OFF] = "Disattivato", [UI_MENU_UPSCALING_AUTO] = "Automatico",
    [UI_MENU_UPSCALING_UNAVAILABLE] = "non disponibile qui",
    [UI_MENU_UPSCALING_UNTIL] = "%s fino al riavvio",
    [UI_MENU_UPSCALING_QUALITY] = "Upscaling per le prestazioni",
    [UI_MENU_UPSCALING_QUALITY_DESC] = "Dimensioni a cui viene disegnata la scena 3D prima che l'upscaler la porti alla "
                                       "risoluzione del gioco (indicate sotto il valore). Nativa la disegna a grandezza "
                                       "piena, la più nitida (DLAA con DLSS). Qualità, Bilanciata, Prestazioni e Ultra "
                                       "prestazioni la disegnano a circa il 67, 58, 50 e 33 % per più FPS; Ultra prestazioni "
                                       "è per 3840 x 2160. Si applica dopo il riavvio.",
    [UI_MENU_UPSCALING_NATIVE] = "Disattivato (risoluzione piena)", [UI_MENU_DLSS_QUALITY] = "Qualità", [UI_MENU_DLSS_BALANCED] = "Bilanciata",
    [UI_MENU_DLSS_PERFORMANCE] = "Prestazioni", [UI_MENU_UPSCALING_ULTRA] = "Ultra prestazioni",
    [UI_MENU_UPSCALING_MODE_OFF] = "senza upscaler",
    [UI_MENU_AA] = "Antialiasing (SMAA)",
    [UI_MENU_AA_DESC] = "SMAA ammorbidisce i bordi scalettati prima di disegnare l'HUD. Alto è il valore predefinito; Ultra "
                        "trova più bordi con un po' più di GPU. Non viene usato mentre è attivo un upscaler.",
    [UI_SNAP_SMAA_LOW] = "Basso", [UI_SNAP_SMAA_MEDIUM] = "Medio", [UI_SNAP_SMAA_HIGH] = "Alto",
    [UI_MENU_AA_OFF] = "Disattivato",
    [UI_MENU_AA_BY_UPSCALER] = "l'upscaler ammorbidisce i bordi",
    [UI_SNAP_RES] = "Risoluzione interna del gioco",
    [UI_SNAP_RES_DESC] = "Risoluzione a cui viene disegnata la scena 3D. 100 % è il 1920 x 1080 proprio del gioco: riducila "
                         "per un'immagine più leggera, aumentala (supersampling) per una più nitida che costa tempo di GPU. "
                         "«In base allo schermo» eguaglia l'altezza dello schermo o della finestra. Funziona insieme "
                         "all'antialiasing. Si applica dopo il riavvio.",
    [UI_SNAP_RES_UPSCALER] = "oltre il 100 %: imposta l'upscaling per le prestazioni su Disattivato",
    [UI_SNAP_FG] = "Generazione di fotogrammi",
    [UI_SNAP_FG_DESC] = "Generazione di fotogrammi AMD FSR: un fotogramma generato ogni due reali. L'interfaccia resta "
                        "fuori dall'interpolazione. Si mette in pausa da sola mentre il gioco va più veloce di metà della "
                        "frequenza di aggiornamento del monitor. Le informazioni sulle prestazioni mostrano gli FPS reali e "
                        "quelli generati. Si applica dopo il riavvio.",
    [UI_SNAP_FG_NEEDS] = "richiede AMD FSR 3.1, FSR 4 o NVIDIA DLSS come upscaler",
    [UI_SNAP_HDPH] = "Miniature delle foto in HD",
    [UI_SNAP_HDPH_DESC] = "L'anteprima dopo uno scatto e le foto nelle cartelle e nella selezione usano la foto a "
                          "1080 x 720 invece della miniatura a 360 x 240 del gioco. Le foto salvate e il punteggio non "
                          "cambiano.",
    [UI_SNAP_SHADOW] = "Risoluzione delle ombre",
    [UI_SNAP_SHADOW_DESC] = "Ingrandisce tutte le mappe delle ombre del gioco. Auto segue la risoluzione 3D: 2x a 1080p, 3x "
                            "al 125-150 %, 4x dal 200 %. Le ombre dipinte nello scenario non cambiano. Si applica dopo il "
                            "riavvio.",
    [UI_SNAP_TEXPACK] = "Pacchetto di texture HD",
    [UI_SNAP_TEXPACK_DESC] = "Usa le texture HD della cartella texpack accanto al gioco, create su questo PC a partire dal "
                             "tuo gioco. Si applica dopo il riavvio.",
    [UI_SNAP_TEXPACK_NONE] = "nessun pacchetto nella cartella texpack",
    [UI_SNAP_HDSH] = "Modalità Ombre HD (sperimentale)",
    [UI_SNAP_HDSH_DESC] = "Le ombre di piante, rocce, scale e scenario sono dipinte nelle texture di ogni livello. "
                          "Attivato: il launcher le legge dal tuo gioco e le ingrandisce su questo PC per tutti i "
                          "livelli («Genera ombre HD»; parte da solo all'apertura del launcher); si vedono al termine. Anche "
                          "le ombre in tempo reale passano alla loro mappa più grande (disattivato, seguono la risoluzione "
                          "interna). Si applica dopo il riavvio.",
    [UI_SNAP_UIMOTION] = "Menu e interfaccia fluidi (sperimentale)",
    [UI_SNAP_UIMOTION_DESC] = "Oltre i 60 FPS il movimento dei menu e dell'interfaccia viene disegnato a ogni fotogramma invece "
                              "che in 60 passi al secondo. La logica del gioco non cambia. Disattivalo se un menu appare doppio "
                              "o sfarfalla. Si applica dopo il riavvio.",
    [UI_SNAP_TAB] = "Migliorie",
    [UI_SNAP_ENH] = "Migliorie di NewSnap (non cambiano la logica del gioco)",
    [UI_SNAP_ASPECT] = "Proporzioni",
    [UI_SNAP_ASPECT_DESC] = "Mantieni 16:9 aggiunge bande sugli schermi più larghi; Allunga riempie la finestra; Ultrawide "
                            "estende la vista 3D alla finestra con le proporzioni del gioco, lascia l'interfaccia al centro "
                            "e scatta le foto con la consueta vista 16:9 (sperimentale).",
    [UI_SNAP_TAB_SYS] = "Sistema",
    [UI_SNAP_SYS_CONT] = "Torna al gioco",
    [UI_SNAP_SYS_CONT_DESC] = "Chiude questo menu e riprende a giocare.",
    [UI_SNAP_SYS_RESTART] = "Riavvia il gioco",
    [UI_SNAP_SYS_RESTART_DESC] = "Chiude il gioco e lo riapre, per le impostazioni che si applicano dopo il riavvio. I "
                                 "progressi successivi all'ultimo salvataggio vanno persi.",
    [UI_SNAP_SYS_QUIT] = "Esci al desktop",
    [UI_SNAP_SYS_QUIT_DESC] = "Chiude il gioco. I progressi successivi all'ultimo salvataggio vanno persi; il gioco salva "
                              "solo dopo ogni spedizione.",
    [UI_MENU_OUTPUT_RES_AUTO] = "Automatica",
    [UI_MENU_OUTPUT_RES_NEXT] = ", %s dopo il riavvio",

    [UI_MENU_FPS_LIMIT] = "Limite di FPS",
    [UI_MENU_FPS_LIMIT_DESC] = "Limite dei fotogrammi: 30, 60 (predefinito), 90, 120 o 144 FPS, oppure VRR (appena sotto la "
                               "frequenza di aggiornamento del monitor). Le scene native più lente mantengono il loro ritmo. "
                               "Si applica subito; gli FPS ottenuti dipendono dalla GPU e dalla modalità dello schermo.",
    [UI_MENU_FPS_30] = "30 FPS", [UI_MENU_FPS_60] = "60 FPS",
    [UI_MENU_REALTIME] = "Velocità del gioco in base all'orologio",
    [UI_MENU_REALTIME_DESC] = "Fa avanzare il gioco in base al tempo reale, così un fotogramma lento non lo rallenta.",
    [UI_MENU_CLOTH_REALTIME] = "Tessuti in base all'orologio",
    [UI_MENU_CLOTH_REALTIME_DESC] = "Fa avanzare in base al tempo reale anche tessuti e capelli.",
    [UI_MENU_HIGHFPS_FIX] = "Correzioni per FPS elevati",
    [UI_MENU_HIGHFPS_FIX_DESC] = "Corregge la fisica che non funziona oltre i 30 FPS e gli oggetti che diventano trasparenti "
                                 "o invisibili oltre i 60.",
    [UI_MENU_GAME_LANG] = "Lingua del gioco", [UI_MENU_GAME_LANG_DESC] = "Lingua dei testi e delle voci del gioco.",
    [UI_MENU_GAME_LANG_AUTO] = "Automatica",
    [UI_MENU_OPERATION_MODE] = "Modalità della console",
    [UI_MENU_OPERATION_MODE_DESC] = "Se il gioco crede di essere nella base (TV) o in modalità portatile.",
    [UI_MENU_MODE_DOCKED] = "TV (base)", [UI_MENU_MODE_HANDHELD] = "Portatile",
    [UI_MENU_HUD] = "HUD",
    [UI_MENU_HUD_DESC] = "Disattivato, l'HUD del gioco non viene disegnato mentre giochi; i menu restano. F12 lo attiva o "
                         "disattiva.",
    [UI_MENU_ASSUME_FOCUS] = "Continua senza focus",
    [UI_MENU_ASSUME_FOCUS_DESC] = "Attivato (predefinito), il gioco continua mentre sei in un'altra finestra e la tastiera "
                                  "non ha effetto finché la finestra non torna in primo piano. Disattivato, va in pausa "
                                  "quando la sua finestra perde il focus, come su Switch premendo Home; un caricamento "
                                  "interrotto così può restare bloccato.",

    [UI_MENU_MODS_INSTALLED] = "Mod installate",
    [UI_MENU_MODS_NONE] = "Non ci sono ancora mod. Estrai una mod nella cartella mods, una cartella per mod con dentro la "
                          "sua cartella romfs, e riavvia il gioco.",
    [UI_MENU_MODS_OPEN] = "Apri la cartella delle mod",
    [UI_MENU_MODS_OPEN_DESC] = "Mostra la cartella da cui il gioco carica le mod. Viene creata se non esiste.",
    [UI_MENU_MODS_ROW_DESC] = "File del gioco che sostituisce: %u. File nuovi che aggiunge: %u.",
    [UI_MENU_MODS_OVERRIDDEN] = "%u dei suoi file provengono da %s, che è più in alto nell'elenco.",
    [UI_MENU_MODS_MOVE_HINT] = "Il pulsante superiore o Ctrl+Su la sposta in alto, il pulsante sinistro o Ctrl+Giù in basso. "
                               "Quando due mod modificano lo stesso file, vince quella più in alto. Le modifiche si "
                               "applicano dopo il riavvio.",
    [UI_MENU_MODS_EMPTY] = "Questa cartella non contiene file romfs, exefs né cheats.",
    [UI_MENU_MODS_SUBSDK] = "Questa mod include codice di gioco proprio (un plugin subsdk o un main sostituito). Il port non "
                            "può caricare moduli di codice, quindi l'intera mod resta disattivata.",
    [UI_MENU_MODS_EXEFS_LATER] = "Questa mod modifica il codice del gioco (exefs). Il gioco integra le patch al prossimo "
                                 "avvio (una ricostruzione di qualche minuto); fino ad allora l'intera mod resta disattivata.",
    [UI_MENU_MODS_CHEATS] = "Trucchi: %d.",
    [UI_MENU_MODS_CHEATS_FILE] = "I trucchi di questa versione del gioco vengono letti all'avvio da cheats\\%s in questa mod.",
    [UI_MENU_MODS_BAD_NAME] = "Il nome della cartella contiene |, che l'elenco delle mod usa tra un nome e l'altro. Rinomina "
                              "la cartella.",
    [UI_MENU_MODS_OTHER_VERSION] = "%u dei suoi file sono per un'altra versione del gioco e vengono ignorati. Cerca una "
                                   "versione di questa mod fatta per la tua versione del gioco.",
    [UI_MENU_MODS_UNUSED] = "non usata",

    [UI_MENU_VOLUME] = "Volume", [UI_MENU_VOLUME_DESC] = "Volume generale del gioco.",

    [UI_MENU_MOTION] = "Comandi di movimento", [UI_MENU_MOTION_DESC] = "Mira con il giroscopio del controller.",
    [UI_MENU_RUMBLE_STRENGTH] = "Intensità della vibrazione",
    [UI_MENU_RUMBLE_STRENGTH_DESC] = "Con quanta forza vibra il controller.",
    [UI_MENU_RUMBLE_CURVE] = "Curva della vibrazione",
    [UI_MENU_RUMBLE_CURVE_DESC] = "Valori più bassi rafforzano le vibrazioni leggere.",
    [UI_MENU_RUMBLE_TRIGGERS] = "Vibrazione dei grilletti (Xbox)",
    [UI_MENU_RUMBLE_TRIGGERS_DESC] = "Fa vibrare anche i grilletti di un controller Xbox.",
    [UI_MENU_PAD_LAYOUT] = "Disposizione dei pulsanti",
    [UI_MENU_PAD_LAYOUT_DESC] = "Quale pulsante è A. Nintendo: quello a destra, come su Switch. Xbox: quello in basso, come "
                                "su un controller Xbox. PlayStation: quello in basso (croce) e gli altri per posizione, per "
                                "la mod dei pulsanti PlayStation. «Automatica» sceglie Nintendo per i controller con "
                                "etichette Nintendo, PlayStation per i controller PlayStation e Xbox per gli altri. Quale "
                                "controller mostrano le icone del gioco si sceglie in Icone dei pulsanti.",
    [UI_MENU_PAD_LAYOUT_AUTO] = "Automatica", [UI_MENU_PAD_LAYOUT_NINTENDO] = "Nintendo (A a destra)",
    [UI_MENU_PAD_LAYOUT_XBOX] = "Xbox (A in basso)", [UI_MENU_PAD_LAYOUT_PLAYSTATION] = "PlayStation (A in basso)",
    [UI_MENU_PAD_LAYOUT_IN_USE] = "in uso: %s",
    [UI_MENU_PROMPTS] = "Icone dei pulsanti",
    [UI_MENU_PROMPTS_DESC] = "Quali pulsanti del controller mostrano le icone del gioco. «Automatico» segue il controller in "
                             "uso. Nintendo: quelli del gioco. Xbox e PlayStation: mod dei pulsanti disegnate per ogni "
                             "disposizione. Il gioco legge le sue icone all'avvio, quindi cambiano dopo il riavvio.",
    [UI_MENU_PROMPTS_AUTO] = "Automatico", [UI_MENU_PROMPTS_NINTENDO] = "Nintendo", [UI_MENU_PROMPTS_XBOX] = "Xbox",
    [UI_MENU_PROMPTS_PLAYSTATION] = "PlayStation",
    [UI_MENU_PROMPTS_MISSING] = "mancano i file delle icone: esegui di nuovo l'installazione",
    [UI_MENU_PROMPTS_FAILED] = "file delle icone danneggiati: esegui di nuovo l'installazione",
    [UI_MENU_PROMPTS_RESTART] = "le icone cambiano dopo il riavvio",
    [UI_MENU_PROMPTS_OFF_SHAPE] = "disattivato con una risoluzione del gioco diversa da 16:9",
    [UI_MENU_PROMPTS_OFF_MODS] = "disattivato: una mod RomFS sostituisce i suoi file",
    [UI_MENU_PROMPTS_OFF_PATCHES] = "disattivato finché AC_ROMFS_PATCHES è definita",
    [UI_MENU_RESTART] = "Riavvia ora",
    [UI_MENU_RESTART_DESC] = "Chiude il gioco e lo riapre con le nuove icone. I progressi successivi all'ultimo salvataggio "
                             "vanno persi.",
    [UI_MENU_RESTART_CONFIRM] = "Riavviare il gioco ora? I progressi successivi all'ultimo salvataggio vanno persi.",
    [UI_MENU_RESTART_YES] = "Riavvia",
    [UI_MENU_RESTART_SAVING] = "Il gioco sta salvando: potrai riavviare tra un momento.",
    [UI_MENU_LSTICK_DEADZONE] = "Zona morta della levetta sinistra", [UI_MENU_RSTICK_DEADZONE] = "Zona morta della levetta destra",
    [UI_MENU_STICK_DEADZONE_DESC] = "Di quanto si muove una levetta prima che il gioco se ne accorga. Aumentala se il "
                                    "personaggio o la telecamera si muovono da soli: rilascia la levetta, guarda «levetta "
                                    "ora» e imposta la zona morta qualche punto più in alto.",
    [UI_MENU_STICK_DEADZONE_NOW] = "levetta ora: %.0f %%",
    [UI_MENU_MOUSE_SENS] = "Sensibilità del mouse",
    [UI_MENU_MOUSE_SENS_DESC] = "Quanto velocemente ruota la telecamera con il mouse.",
    [UI_MENU_WALK_KEY] = "Tasto per camminare",
    [UI_MENU_WALK_KEY_DESC] = "Tenendolo premuto, le levette della tastiera si inclinano solo in parte, per camminare "
                              "invece di correre. La scala di camminata stabilisce di quanto. Non ha effetto su controller "
                              "e mouse.",
    [UI_MENU_WALK_KEY_TAKEN] = "anche %s",
    [UI_MENU_WALK_SCALE] = "Scala di camminata",
    [UI_MENU_WALK_SCALE_DESC] = "Inclinazione delle levette della tastiera con il tasto per camminare. Metà è camminare, il "
                                "massimo è correre.",
    [UI_MENU_STICK_SENS] = "Velocità della telecamera con la levetta",
    [UI_MENU_STICK_SENS_DESC] = "Moltiplica la velocità della telecamera della levetta destra del gioco, massima inclusa, in "
                                "ognuna delle sue cinque sensibilità. Il mouse ha una sua impostazione.",

    [UI_BINDS_HELP] = "Scegli una casella e premi A o Invio, poi il tasto, il pulsante del mouse o il pulsante del "
                      "controller. Canc o X svuota una casella. Un tasto già in uso viene spostato qui; un pulsante del "
                      "controller viene scambiato con quello che sostituisce.",
    [UI_BINDS_COL_KEY1] = "Tasto 1", [UI_BINDS_COL_KEY2] = "Tasto 2", [UI_BINDS_COL_PAD] = "Controller",
    [UI_BINDS_GROUP_BUTTONS] = "Pulsanti", [UI_BINDS_GROUP_MOVE] = "Movimento", [UI_BINDS_GROUP_CAMERA] = "Telecamera",
    [UI_BINDS_PRESS_KEY] = "Premi un tasto o un pulsante del mouse per %s",
    [UI_BINDS_PRESS_PAD] = "Premi un pulsante del controller per %s",
    [UI_BINDS_CANCEL_HINT] = "Esc annulla, oppure attendi %d s",
    [UI_BINDS_TAKEN] = "%s rimosso da %s", [UI_BINDS_SWAPPED] = "%s scambiato con %s",
    [UI_BINDS_RESET] = "Ripristina tutti i pulsanti",
    [UI_BINDS_RESET_DESC] = "Torna ai tasti e ai pulsanti predefiniti. La disposizione qui sopra viene applicata di nuovo: i "
                            "pulsanti del controller riassegnati restano dove li hai messi fino a questo ripristino.",
    [UI_BIND_A] = "A", [UI_BIND_B] = "B", [UI_BIND_X] = "X", [UI_BIND_Y] = "Y",
    [UI_BIND_LCLICK] = "Premere levetta sinistra", [UI_BIND_RCLICK] = "Premere levetta destra", [UI_BIND_L] = "L",
    [UI_BIND_R] = "R", [UI_BIND_ZL] = "ZL", [UI_BIND_ZR] = "ZR", [UI_BIND_PLUS] = "Più (+)", [UI_BIND_MINUS] = "Meno (-)",
    [UI_BIND_LEFT] = "Croce direzionale sinistra", [UI_BIND_UP] = "Croce direzionale su",
    [UI_BIND_RIGHT] = "Croce direzionale destra",
    [UI_BIND_DOWN] = "Croce direzionale giù",
    [UI_BIND_LSTICK_LEFT] = "Muovi a sinistra", [UI_BIND_LSTICK_UP] = "Muovi in avanti",
    [UI_BIND_LSTICK_RIGHT] = "Muovi a destra", [UI_BIND_LSTICK_DOWN] = "Muovi indietro",
    [UI_BIND_RSTICK_LEFT] = "Telecamera a sinistra", [UI_BIND_RSTICK_UP] = "Telecamera su",
    [UI_BIND_RSTICK_RIGHT] = "Telecamera a destra", [UI_BIND_RSTICK_DOWN] = "Telecamera giù",
    [UI_BIND_DESC_A] = "Interagire, raccogliere, parlare.", [UI_BIND_DESC_B] = "Correre, annullare, tornare indietro.",
    [UI_BIND_DESC_X] = "Saltare.", [UI_BIND_DESC_Y] = "Attaccare.", [UI_BIND_DESC_LCLICK] = "Accovacciarsi.",
    [UI_BIND_DESC_RCLICK] = "Visuale in prima persona.", [UI_BIND_DESC_L] = "Abilità.",
    [UI_BIND_DESC_R] = "Lanciare.", [UI_BIND_DESC_ZL] = "Scudo, agganciare.", [UI_BIND_DESC_ZR] = "Arco.",
    [UI_BIND_DESC_PLUS] = "Menu, inventario.", [UI_BIND_DESC_MINUS] = "Mappa.",
    [UI_BIND_DESC_DPAD] = "Selezione rapida.",
    [UI_BIND_DESC_MOVE] = "Muove come la levetta sinistra. Anche la levetta sinistra del controller funziona sempre.",
    [UI_BIND_DESC_CAMERA] = "Ruota la telecamera come la levetta destra. Anche il mouse e la levetta destra del controller "
                            "funzionano sempre.",
    [UI_KEY_SPACE] = "Spazio", [UI_KEY_TAB] = "Tab", [UI_KEY_LSHIFT] = "Maiusc sx", [UI_KEY_LCTRL] = "Ctrl sx",
    [UI_KEY_UP] = "Freccia su", [UI_KEY_DOWN] = "Freccia giù", [UI_KEY_LEFT] = "Freccia sinistra",
    [UI_KEY_RIGHT] = "Freccia destra",
    [UI_KEY_MOUSE_L] = "Clic sinistro", [UI_KEY_MOUSE_R] = "Clic destro", [UI_KEY_MOUSE_M] = "Clic centrale",
    [UI_KEY_MOUSE_X1] = "Mouse 4", [UI_KEY_MOUSE_X2] = "Mouse 5",
    [UI_KEY_ENTER] = "Invio", [UI_KEY_BACKSPACE] = "Backspace", [UI_KEY_RSHIFT] = "Maiusc dx",
    [UI_KEY_RCTRL] = "Ctrl dx", [UI_KEY_LALT] = "Alt", [UI_KEY_CAPSLOCK] = "Bloc Maiusc", [UI_KEY_INSERT] = "Ins",
    [UI_KEY_DELETE] = "Canc", [UI_KEY_HOME] = "Home", [UI_KEY_END] = "Fine", [UI_KEY_PAGEUP] = "Pag su",
    [UI_KEY_PAGEDOWN] = "Pag giù", [UI_KEY_NUM_FMT] = "Num %s",
    [UI_PAD_SOUTH] = "Pulsante inferiore", [UI_PAD_EAST] = "Pulsante destro", [UI_PAD_WEST] = "Pulsante sinistro",
    [UI_PAD_NORTH] = "Pulsante superiore", [UI_PAD_LSTICK] = "Levetta sinistra", [UI_PAD_RSTICK] = "Levetta destra",
    [UI_PAD_L] = "Dorsale sinistro", [UI_PAD_R] = "Dorsale destro", [UI_PAD_START] = "Start",
    [UI_PAD_BACK] = "Back",
    [UI_PAD_DPAD_LEFT] = "Croce direzionale sinistra", [UI_PAD_DPAD_UP] = "Croce direzionale su",
    [UI_PAD_DPAD_RIGHT] = "Croce direzionale destra",
    [UI_PAD_DPAD_DOWN] = "Croce direzionale giù", [UI_PAD_ZL] = "Grilletto sinistro", [UI_PAD_ZR] = "Grilletto destro",
    [UI_PAD_LPADDLE1] = "Pulsante posteriore sinistro", [UI_PAD_RPADDLE1] = "Pulsante posteriore destro",
    [UI_PAD_LPADDLE2] = "Pulsante posteriore sinistro 2", [UI_PAD_RPADDLE2] = "Pulsante posteriore destro 2",
    [UI_PAD_CROSS] = "Croce", [UI_PAD_CIRCLE] = "Cerchio", [UI_PAD_SQUARE] = "Quadrato", [UI_PAD_TRIANGLE] = "Triangolo",

    [UI_MENU_MENU_LANG] = "Lingua del menu", [UI_MENU_MENU_LANG_DESC] = "Lingua di questo menu e delle informazioni a schermo.",
    [UI_MENU_MENU_LANG_AUTO] = "Automatica (di Windows)",

    [UI_MENU_ADV_WARNING] = "Queste impostazioni servono per i test e per risolvere problemi. Modificale solo se sai perché.",
    [UI_MENU_GROUP_SCHED] = "Pianificazione", [UI_MENU_GROUP_SHADERS] = "Shader e pipeline",
    [UI_MENU_GROUP_TEXMEM] = "Texture e memoria", [UI_MENU_GROUP_FIXES] = "Correzioni di rendering",
    [UI_MENU_GROUP_VULKAN] = "Vulkan", [UI_MENU_GROUP_DIAG] = "Diagnostica",
    [UI_MENU_ASYNC_PREEMPT] = "Prelazione dei core virtuali",
    [UI_MENU_ASYNC_PREEMPT_DESC] = "Permette a un thread del gioco di interromperne un altro sullo stesso core virtuale.",
    [UI_MENU_PREEMPT_OFF] = "Disattivata", [UI_MENU_PREEMPT_ON] = "Attivata", [UI_MENU_PREEMPT_INHERIT] = "Solo ereditarietà",
    [UI_MENU_REPLAY_ASYNC] = "Prepara i fotogrammi in un thread proprio",
    [UI_MENU_REPLAY_ASYNC_DESC] = "Prepara i fotogrammi per la GPU in un thread separato invece che nel thread del gioco. "
                                  "Aggiunge fino a un fotogramma di latenza.",
    [UI_MENU_TIMER_1MS] = "Timer di Windows a 1 ms",
    [UI_MENU_TIMER_1MS_DESC] = "Porta la risoluzione del timer di sistema a 1 ms per un ritmo dei fotogrammi più stabile.",
    [UI_MENU_PIPE_WAIT] = "Gestione dei disegni in attesa",
    [UI_MENU_PIPE_WAIT_DESC] = "Predefinita mantiene la pianificazione attuale con un worker riservato ai disegni in "
                               "attesa; Vecchia (disegno) usa la pianificazione precedente.",
    [UI_MENU_PIPE_WAIT_DEFAULT] = "Predefinita", [UI_MENU_PIPE_WAIT_DRAW] = "Vecchia (disegno)",
    [UI_MENU_PIPE_SKIP] = "Disegni saltati mentre si crea una pipeline",
    [UI_MENU_PIPE_SKIP_DESC] = "Quali disegni vengono scartati invece di attendere la loro pipeline.",
    [UI_MENU_PIPE_SKIP_STRICT] = "Rigoroso", [UI_MENU_PIPE_SKIP_ANY] = "Qualsiasi",
    [UI_MENU_PIPE_SKIP_FULLSCREEN] = "Passate a schermo intero",
    [UI_MENU_LIB_PREBUILD] = "Precompila le librerie di stadi",
    [UI_MENU_LIB_PREBUILD_DESC] = "Compila in anticipo e in background le librerie di stadi degli shader.",
    [UI_MENU_LIB_PREBUILD_THREADS] = "Thread di precompilazione delle librerie",
    [UI_MENU_LIB_PREBUILD_THREADS_DESC] = "Thread usati per precompilare; «Automatico» sceglie un numero in base alla tua CPU.",
    [UI_MENU_PIPE_PREBUILD] = "Precompila le pipeline",
    [UI_MENU_PIPE_PREBUILD_DESC] = "Compila in anticipo le pipeline note.",
    [UI_MENU_PREWARM_XLATE] = "Preriscalda il traduttore",
    [UI_MENU_PREWARM_XLATE_DESC] = "Thread che traducono gli shader noti all'avvio; «Automatico» usa metà dei thread della "
                                   "CPU, al massimo 16.",
    [UI_MENU_GPL] = "Libreria di pipeline grafiche",
    [UI_MENU_GPL_DESC] = "Usa l'estensione Vulkan per le librerie di pipeline; disattivala se il tuo driver ha problemi.",
    [UI_MENU_ASTC] = "Decodifica delle texture ASTC",
    [UI_MENU_ASTC_DESC] = "Dove vengono decodificate le texture compresse ASTC.",
    [UI_MENU_ASTC_AUTO] = "Automatica", [UI_MENU_ASTC_GPU] = "Shader della GPU", [UI_MENU_ASTC_NATIVE] = "Nativa",
    [UI_MENU_ASTC_CPU] = "CPU",
    [UI_MENU_MEMORY] = "Modalità di memoria della GPU",
    [UI_MENU_MEMORY_DESC] = "Come la memoria del gioco viene condivisa con la GPU.",
    [UI_MENU_MEMORY_AUTO] = "Automatica", [UI_MENU_MEMORY_IMPORT] = "Importazione", [UI_MENU_MEMORY_MIRROR] = "Specchio",
    [UI_MENU_MEMORY_VERIFY] = "Verifica",
    [UI_MENU_TEX_ALIAS] = "Alias delle texture",
    [UI_MENU_TEX_ALIAS_DESC] = "Una texture nuova creata sulla memoria di un'altra ancora attiva parte con quel contenuto "
                               "invece che vuota.",
    [UI_MENU_TEX_VRAM_PRESSURE] = "Limite di memoria delle texture",
    [UI_MENU_TEX_VRAM_PRESSURE_DESC] = "Percentuale di memoria video oltre la quale vengono scartate le texture che il "
                                       "gioco ha liberato (tornano dall'archiviazione quando servono). 0 le conserva.",
    [UI_MENU_ASTC_BC] = "Comprimi ASTC in BC",
    [UI_MENU_ASTC_BC_DESC] = "Con il decodificatore della GPU: ricodifica le texture ASTC decodificate in BC1 se sono "
                             "opache e in BC3 altrimenti, tra un quarto e un ottavo della memoria video. Per GPU con 4 GB o "
                             "meno; le texture appaiono un po' più a blocchi.",
    [UI_MENU_LOD_GUARD] = "Protezione del LOD",
    [UI_MENU_LOD_GUARD_DESC] = "Evita che gli oggetti sfarfallino in un punto sbagliato o che lo sfondo lontano resti piatto "
                               "per un fotogramma, attendendo che il gioco finisca di riscrivere i livelli di dettaglio "
                               "prima che la GPU li legga.",
    [UI_MENU_FIX_C0] = "Correzione del buffer delle costanti",
    [UI_MENU_FIX_C0_DESC] = "Riempie il banco di costanti c0 riservato del driver (dimensioni di archiviazione, dimensione "
                            "di dispatch, dimensione del punto, istanza base) invece di leggere zeri.",
    [UI_MENU_FIX_ZERO] = "Azzera la nuova memoria della GPU",
    [UI_MENU_FIX_ZERO_DESC] = "I nuovi blocchi di memoria della GPU partono azzerati, come la memoria di Switch.",
    [UI_MENU_BIND_SKIP] = "Salta i binding ripetuti",
    [UI_MENU_BIND_SKIP_DESC] = "Ottimizzazione: salta i binding che non sono cambiati.",
    [UI_MENU_SHADER_MEMO] = "Memoria degli shader", [UI_MENU_SHADER_MEMO_DESC] = "Ottimizzazione: ricorda le ricerche degli shader.",
    [UI_MENU_PIPE_MEMO] = "Memoria delle pipeline",
    [UI_MENU_PIPE_MEMO_DESC] = "Ottimizzazione: riutilizza la pipeline del disegno precedente quando il suo stato si ripete.",
    [UI_MENU_TEX_MEMO] = "Memoria dei binding delle texture",
    [UI_MENU_TEX_MEMO_DESC] = "Ottimizzazione: ricorda i descrittori delle texture tra un disegno e l'altro.",
    [UI_MENU_DESC_TEMPLATE] = "Modelli di descrittori",
    [UI_MENU_DESC_TEMPLATE_DESC] = "Ottimizzazione: aggiorna i descrittori in blocco.",
    [UI_MENU_PUSH_SKIP] = "Salta le push constant ripetute",
    [UI_MENU_PUSH_SKIP_DESC] = "Ottimizzazione: salta le push constant che non sono cambiate.",
    [UI_MENU_SPLIT_DRAWS] = "Invio anticipato alla GPU",
    [UI_MENU_SPLIT_DRAWS_DESC] = "Invia il lavoro della GPU a parti ogni N disegni tra una passata e l'altra, così la GPU "
                                 "inizia prima; 0 lo disattiva.",
    [UI_MENU_VK_VALIDATION] = "Layer di validazione",
    [UI_MENU_VK_VALIDATION_DESC] = "Controlla ogni chiamata Vulkan e rallenta molto il gioco.",
    [UI_MENU_VK_VALIDATION_MISSING] = "Il layer di validazione non è installato.",
    [UI_MENU_VK_DYN_VERTEX] = "Stato dei vertici dinamico",
    [UI_MENU_VK_DYN_VERTEX_DESC] = "Forza l'input dei vertici dinamico su attivato o disattivato; il valore predefinito "
                                   "dipende dalla GPU.",
    [UI_MENU_VK_DYN_A2C] = "Alpha to coverage dinamico",
    [UI_MENU_VK_DYN_A2C_DESC] = "Forza l'alpha to coverage dinamico su attivato o disattivato. Predefinito: disattivato con "
                                "il driver AMD per RDNA 2 e precedenti, che con esso disegna i personaggi in nero; attivato "
                                "negli altri casi.",
    [UI_MENU_VK_SUBGROUP_PIN] = "Fissa la dimensione del sottogruppo",
    [UI_MENU_VK_SUBGROUP_PIN_DESC] = "Fissa la dimensione del sottogruppo degli shader.",
    [UI_MENU_TRACE] = "Registro delle prestazioni", [UI_MENU_TRACE_DESC] = "Scrive i tempi dei fotogrammi in un file.",
    [UI_MENU_FLIGHT] = "Registratore di volo",
    [UI_MENU_FLIGHT_DESC] = "Conserva una breve cronologia e la scrive quando un fotogramma si blocca.",
    [UI_MENU_FLIGHT_SPIKE_MS] = "Soglia di blocco (ms)",
    [UI_MENU_FLIGHT_SPIKE_MS_DESC] = "Tempo di fotogramma che conta come blocco.",
    [UI_MENU_INPUT_RECORD] = "Registra l'input",
    [UI_MENU_INPUT_RECORD_DESC] = "Scrive i tuoi input in un file per segnalare errori.",
    [UI_MENU_OPEN_LOG] = "Apri la cartella dei registri", [UI_MENU_OPEN_LOG_DESC] = "Mostra la cartella con i registri.",
    [UI_MENU_COPY_INFO] = "Copia le informazioni di sistema",
    [UI_MENU_COPY_INFO_DESC] = "Copia negli appunti GPU, driver, CPU, RAM e le impostazioni modificate.",
    [UI_MENU_COPY_INFO_DONE] = "Copiato", [UI_MENU_ACTION_FAILED] = "non riuscito",
    [UI_MENU_RESET] = "Ripristina tutte le impostazioni", [UI_MENU_RESET_DESC] = "Si applica a tutte le schede.",
    [UI_MENU_RESET_CONFIRM] = "Ripristinare tutte le impostazioni ai valori predefiniti?",
    [UI_MENU_RESET_YES] = "Ripristina",
    [UI_MENU_RESET_NO] = "Annulla",

    [UI_MENU_OV_FPS] = "%.0f FPS", [UI_MENU_OV_FRAME_MS] = "%.1f ms", [UI_MENU_OV_GAME_PCT] = "gioco %.0f%%",
    [UI_MENU_OV_MAX_MS] = "max %.1f ms",
    [UI_MENU_OV_GPU] = "GPU", [UI_MENU_OV_CPU] = "CPU", [UI_MENU_OV_RAM] = "RAM", [UI_MENU_OV_VRAM] = "VRAM",
    [UI_MENU_OV_TEMP] = "Temperatura", [UI_MENU_OV_POWER] = "Consumo", [UI_MENU_OV_CLOCK] = "Frequenza",
    [UI_MENU_OV_NONE] = "-",
    [UI_MENU_OV_REPLAY] = "Preparazione dei fotogrammi", [UI_MENU_OV_GPU_TIME] = "GPU occupata per fotogramma",
    [UI_MENU_OV_PIPE_WAIT] = "Attese delle pipeline",
    [UI_MENU_OV_SHADER_WAIT] = "Attese degli shader", [UI_MENU_OV_TEX_UPLOADS] = "Caricamenti di texture",
    [UI_MENU_OV_FMT_PCT] = "%.0f%%", [UI_MENU_OV_FMT_TEMP] = "%.0f °C", [UI_MENU_OV_FMT_POWER] = "%.0f W",
    [UI_MENU_OV_FMT_MHZ] = "%.0f MHz", [UI_MENU_OV_FMT_GB] = "%.1f GB", [UI_MENU_OV_FMT_GB_OF] = "/ %.1f GB",
    [UI_MENU_OV_GAME_GB] = "gioco %.1f GB", [UI_MENU_OV_FMT_MS] = "%.2f ms", [UI_MENU_OV_PER_FRAME] = "%.1f per fotogramma",
    [UI_MENU_OV_WINDOW] = "Finestra", [UI_MENU_OV_OUTPUT] = "Immagine del gioco", [UI_MENU_OV_SCENE] = "Scena 3D",
    [UI_MENU_OV_SCALING] = "Upscaling", [UI_MENU_OV_LIMIT] = "Limite di FPS", [UI_MENU_OV_PRESENT] = "Presentazione",
    [UI_MENU_OV_TEX] = "Compressione delle texture", [UI_MENU_OV_OS] = "Sistema",
    [UI_MENU_OV_FMT_SIZE] = "%ux%u", [UI_MENU_OV_FMT_SCENE] = "%ux%u, %.0f%%",
    [UI_MENU_OV_FMT_FSR] = "AMD FSR 1, nitidezza %d%%", [UI_MENU_OV_SCALE_NONE] = "nessuno (1:1)",
    [UI_MENU_OV_SCALE_BILINEAR] = "bilineare",
    [UI_MENU_OV_FMT_AREA] = "media d'area, nitidezza %d%%",
    [UI_MENU_OV_FMT_PRESHARP] = "RCAS prima dell'HUD, nitidezza %d%%",
    [UI_MENU_TAB_CHEATS] = "Trucchi",
    [UI_MENU_CHEATS_NONE] = "Non ci sono trucchi per questa versione del gioco. I trucchi di una mod sono un file di "
                            "trucchi di Atmosphere nella sua cartella cheats, con il nome della build del gioco: "
                            "mods\\<mod>\\cheats\\%s. Riavvia il gioco per leggerli. Per i trucchi che modificano il codice "
                            "del gioco, il gioco viene ricostruito all'avvio (qualche minuto).",
    [UI_MENU_CHEATS_MOD] = "%s: %d trucchi",
    [UI_MENU_CHEAT_CODE_DESC] = "Modifica il codice del gioco. Si attiva subito.",
    [UI_MENU_CHEAT_KEY_DESC] = "Modifica il codice del gioco mentre tieni premuto %s. Si attiva subito.",
    [UI_MENU_CHEAT_DATA_DESC] = "Scrive nella memoria del gioco a ogni fotogramma finché è attivato.",
    [UI_MENU_CHEAT_MASTER] = "sempre attivato",
    [UI_MENU_CHEAT_MASTER_DESC] = "Il codice master del file: è sempre attivato.",
    [UI_MENU_CHEAT_RESTORE] = "non necessario",
    [UI_MENU_CHEAT_RESTORE_DESC] = "Riscrive soltanto il codice originale del gioco. Disattivare un trucco lo fa già.",
    [UI_MENU_CHEAT_REBUILD] = "dopo la ricostruzione",
    [UI_MENU_CHEAT_REBUILD_DESC] = "Questo trucco modifica il codice del gioco ed è nuovo o è stato modificato da quando "
                                   "il gioco è stato costruito. Il gioco lo integra al prossimo avvio (qualche minuto), "
                                   "oppure usa Ricostruisci il gioco ora.",
    [UI_MENU_CHEAT_UNSUPPORTED] = "non supportato",
    [UI_MENU_CHEAT_UNSUPPORTED_DESC] = "Questo trucco non può essere usato con questa versione del gioco:",
    [UI_MENU_CHEATS_REBUILD] = "Ricostruisci il gioco ora",
    [UI_MENU_CHEATS_REBUILD_DESC] = "Alcuni trucchi modificano il codice del gioco e non sono integrati: sono nuovi o sono "
                                    "stati modificati, oppure la loro ultima ricostruzione è fallita o è stata annullata. "
                                    "Chiude il gioco; l'installazione li integra (qualche minuto) e riapre il gioco. I "
                                    "progressi successivi all'ultimo salvataggio vanno persi.",
    [UI_MENU_MODS_EXEFS_UNSUPPORTED] = "Questa mod modifica il codice del gioco (exefs) in un modo che il port non può "
                                       "applicare, quindi l'intera mod resta disattivata. %s",
    [UI_MENU_MODS_EXEFS_OTHER] = "Le sue patch di codice (exefs) sono per un'altra versione del gioco.",
    [UI_MENU_MODS_EXEFS_ON] = "Patch di codice in uso: %d file.",
    [UI_MENU_MODS_REPLACES_BUILTIN] = "Patch di codice in uso: %d file. Sostituiscono la patch propria del port %s, che "
                                      "resta disattivata finché questa mod è attivata.",
};
