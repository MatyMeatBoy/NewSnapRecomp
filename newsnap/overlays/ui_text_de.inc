// The in-game menu in German (MENU-LANG-01), every string of text_es (ui_text_es.inc).
// Included by ui_text.c in place of the keyboard-only German row.
static const char *const text_de[UI_TEXT_COUNT] = {
    SWKBD("Texteingabe", "Gib einen Namen ein", "Pferd", "OK", "Abbrechen", "Controller: A = OK, B = Abbrechen"),

    [UI_MENU_TITLE] = "Einstellungen",
    [UI_MENU_TAB_SCREEN] = "Anzeige", [UI_MENU_TAB_GAME] = "Spiel", [UI_MENU_TAB_MODS] = "Mods", [UI_MENU_TAB_SOUND] = "Ton",
    [UI_MENU_TAB_CONTROLS] = "Steuerung", [UI_MENU_TAB_MENU] = "Menü", [UI_MENU_TAB_ADVANCED] = "Erweitert",
    [UI_MENU_CONTINUE] = "Fortsetzen", [UI_MENU_QUIT] = "Spiel beenden",
    [UI_MENU_ON] = "Ein", [UI_MENU_OFF] = "Aus", [UI_MENU_AUTO] = "Automatisch",
    [UI_MENU_DEFAULT_MARK] = "Standard",
    [UI_MENU_AFTER_RESTART] = "nach Neustart", [UI_MENU_SET_BY_ENV] = "durch eine Umgebungsvariable festgelegt",
    [UI_MENU_SAVE_FAILED] = "Einstellungen konnten nicht gespeichert werden",
    [UI_MENU_VERSION] = "NewSnapRecomp %s, Snap %s",

    [UI_MENU_FULLSCREEN] = "Vollbild",
    [UI_MENU_FULLSCREEN_DESC] = "Das Spiel füllt den ganzen Bildschirm; F11 schaltet um.",
    [UI_MENU_WINDOW_SIZE] = "Fenstergröße",
    [UI_MENU_WINDOW_SIZE_DESC] = "Größe des Spielfensters außerhalb des Vollbilds.",
    [UI_MENU_WINDOW_SIZE_CUSTOM] = "Benutzerdefiniert",
    [UI_MENU_PRESENT] = "Bildausgabe", [UI_MENU_PRESENT_DESC] = "Wie die fertigen Frames auf den Bildschirm gelangen.",
    [UI_MENU_PRESENT_MAILBOX] = "Mailbox", [UI_MENU_PRESENT_VSYNC] = "VSync", [UI_MENU_PRESENT_IMMEDIATE] = "Sofort",
    [UI_MENU_PRESENT_IN_USE] = "aktiv: %s",
    [UI_MENU_GPU] = "Grafikkarte", [UI_MENU_GPU_DESC] = "Das Vulkan-Gerät, das das Spiel darstellt.",
    [UI_MENU_GPU_AUTO] = "Automatisch",
    [UI_MENU_PERF_OVERLAY] = "Leistungsanzeige",
    [UI_MENU_PERF_OVERLAY_DESC] = "FPS oben rechts. »Vollständig« zeigt zusätzlich Framezeiten mit Diagramm, Auslastung "
                                  "von CPU, GPU und Speicher, Temperaturen und Wartezeiten des Render-Threads. F10 wechselt "
                                  "den Modus.",
    [UI_MENU_PERF_OFF] = "Ausgeblendet", [UI_MENU_PERF_FPS] = "FPS", [UI_MENU_PERF_FULL] = "Vollständig",
    [UI_PERF_LINE_FPS] = "%.0f fps",
    [UI_MENU_GRAPHICS] = "Bild",
    [UI_MENU_OUTPUT_RES] = "Spielauflösung",
    [UI_MENU_OUTPUT_RES_DESC] = "Größe, in der das Spiel Bild und Oberfläche zeichnet. 1280 x 720 ist am sparsamsten, für "
                                "schwächere GPUs. Über 1920 x 1080 braucht das Spiel mehr Speicher (etwa 240 MB mehr bei "
                                "2560 x 1440, 790 MB bei 3840 x 2160) und GPU-Zeit. Gilt nach einem Neustart. »Automatisch« "
                                "übernimmt die Bildschirmgröße: bis 1920 x 1080, mit aktivem Upscaler bis 3840 x 2160.",
    [UI_MENU_UPSCALER] = "Skalierung aufs Fenster",
    [UI_MENU_UPSCALER_DESC] = "Wie das Bild auf das Fenster skaliert wird. FSR erhält Kanten und Details schärfer als "
                              "bilinear und schärft das Bild auch dann, wenn es schon ins Fenster passt.",
    [UI_MENU_UPSCALER_FSR] = "AMD FSR 1", [UI_MENU_UPSCALER_BILINEAR] = "Bilinear",
    [UI_MENU_FOV] = "Sichtfeld",
    [UI_MENU_FOV_DESC] = "Wie viel von der Welt die Kamera zeigt, in Prozent des Spielwerts (50 Grad vertikal beim "
                         "Spielen). Zwischensequenzen behalten den Bildausschnitt des Spiels.",
    [UI_MENU_ANISO] = "Texturfilterung",
    [UI_MENU_ANISO_DESC] = "Anisotrope Filterung: Boden, Wege und Wände bleiben bei flachem Blickwinkel auch in der Ferne "
                           "scharf, statt zu verschwimmen. Spiel: die Stufe, die das Spiel anfordert, wie auf der Switch. "
                           "Auto: 16x bei 3D-Skalierung von 1440p, das Doppelte der Spielstufe bei 2160p, sonst die des "
                           "Spiels.",
    [UI_MENU_ANISO_GAME] = "Spiel",
    [UI_MENU_ANISO_AUTO] = "Auto",
    [UI_MENU_SHARPNESS] = "FSR-Schärfe",
    [UI_MENU_SHARPNESS_DESC] = "Nachschärfung nach der FSR-Skalierung; 0 schaltet sie aus.",
    [UI_MENU_COLOR] = "Farbe",
    [UI_MENU_COLOR_PRESET] = "Farbprofil",
    [UI_MENU_COLOR_PRESET_DESC] = "Stellt die vier Werte darunter ein. Lebhaft: mehr Kontrast und Sättigung und etwas "
                                  "hellere Schatten (für OLED gedacht). Klarheit: etwas mehr Kontrast, Sättigung und "
                                  "Helligkeit. Änderst du einen Wert, wechselt das Profil zu Benutzerdefiniert. Das HUD "
                                  "ändert sich mit dem Bild, dieses Menü nicht.",
    [UI_MENU_COLOR_DEFAULT] = "Wie im Spiel", [UI_MENU_COLOR_VIVID] = "Lebhaft (OLED)", [UI_MENU_COLOR_CLARITY] = "Klarheit",
    [UI_MENU_COLOR_CUSTOM] = "Benutzerdefiniert",
    [UI_MENU_COLOR_BRIGHTNESS] = "Helligkeit",
    [UI_MENU_COLOR_BRIGHTNESS_DESC] = "Wird zu jeder Farbe addiert; 0 lässt sie unverändert.",
    [UI_MENU_COLOR_CONTRAST] = "Kontrast",
    [UI_MENU_COLOR_CONTRAST_DESC] = "Entfernt die Farben vom mittleren Grau (über 100 %) oder nähert sie an; 100 % lässt "
                                    "sie unverändert.",
    [UI_MENU_COLOR_SATURATION] = "Sättigung",
    [UI_MENU_COLOR_SATURATION_DESC] = "Farbintensität gegenüber Grau; 100 % lässt sie unverändert.",
    [UI_MENU_COLOR_GAMMA] = "Gamma",
    [UI_MENU_COLOR_GAMMA_DESC] = "Unter 1 werden dunkle und mittlere Töne heller, darüber dunkler; 1 lässt sie unverändert.",
    [UI_MENU_HDR_GROUP] = "HDR",
    [UI_MENU_HDR] = "HDR-Ausgabe",
    [UI_MENU_HDR_DESC] = "Intensive Lichter auf einem HDR-Bildschirm. Benötigt aktiviertes HDR in Windows (»HDR "
                         "verwenden«) oder einen Wayland-Compositor mit Farbverwaltung; ohne das bleibt das Bild in SDR. "
                         "Gilt nach einem Neustart. Das Farbprofil oben ist für SDR und wird in HDR nicht verwendet.",
    [UI_MENU_HDR_PEAK] = "Spitzenhelligkeit",
    [UI_MENU_HDR_PEAK_DESC] = "Das Maximum deines Bildschirms in Nits; die hellsten Lichter enden dort.",
    [UI_MENU_HDR_GAME] = "Helligkeit des Spiels",
    [UI_MENU_HDR_GAME_DESC] = "Nits für das Weiß des Bildes (Papierweiß). 203 ist die HDR-Referenz; erhöhe den Wert in "
                              "einem hellen Raum.",
    [UI_MENU_HDR_UI] = "Helligkeit von HUD und Menü",
    [UI_MENU_HDR_UI_DESC] = "Nits für das Weiß des HUD und dieses Menüs.",
    [UI_MENU_HDR_HUE] = "Farbtonkorrektur der Lichter",
    [UI_MENU_HDR_HUE_DESC] = "Intensive Farben wie Feuer oder Funken tendieren zu Weiß wie im SDR-Bild des Spiels, ebenso "
                             "wie das Licht, das sie werfen; 0 lässt sie voll gesättigt.",
    [UI_MENU_SHADOW_SCALE] = "Schattenauflösung",
    [UI_MENU_SHADOW_SCALE_DESC] = "Zeichnet die Schattenkarte der Sonne pro Seite um diesen Faktor größer als die "
                                  "2048x2048 des Spiels: schärfere Schattenkanten und Blätterschatten, auf Kosten von "
                                  "Grafikspeicher (etwa 85 bis 130 MiB bei 2x, 340 bis 520 MiB bei 4x). Gilt ab dem "
                                  "nächsten Start.",
    [UI_MENU_AO] = "Umgebungsverdeckung",
    [UI_MENU_AO_DESC] = "Dunkelt Falten, Ecken und den Boden unter Figuren und Objekten ab, wo wenig Umgebungslicht "
                        "hinkommt. Wird im Bildraum berechnet, nachdem die Welt beleuchtet wurde; das Spiel hat keine "
                        "eigene. »Hoch« kostet mehr GPU-Zeit als »Niedrig«. Gilt sofort.",
    [UI_MENU_AO_OFF] = "Aus",
    [UI_MENU_AO_LOW] = "Niedrig",
    [UI_MENU_AO_HIGH] = "Hoch",
    [UI_MENU_UPSCALING] = "Upscaler (FSR / DLSS)",
    [UI_MENU_UPSCALING_DESC] = "Ein temporaler Upscaler anstelle des Antialiasings des Spiels: weichere Kanten und weniger "
                               "Flimmern, und mit einem Modus unterhalb von Nativ mehr FPS. NVIDIA DLSS benötigt eine "
                               "NVIDIA-RTX-GPU und nvngx_dlss.dll neben newsnap.exe; Intel XeSS eine aktuelle GPU und "
                               "libxess.dll neben newsnap.exe; AMD FSR läuft auf jeder GPU. »Automatisch« nutzt DLSS, wo "
                               "es geht, und sonst FSR. Hier gewähltes DLSS und XeSS gelten nach einem Neustart. Das HUD "
                               "ändert sich nicht.",
    [UI_MENU_UPSCALING_DESC_OTHER] = "Ein temporaler Upscaler anstelle des Antialiasings des Spiels: weichere Kanten und "
                                     "weniger Flimmern, und mit einem Modus unterhalb von Nativ mehr FPS. AMD FSR läuft "
                                     "auf jeder GPU; hier ist »Automatisch« FSR (NVIDIA DLSS und Intel XeSS gibt es nur "
                                     "unter Windows). Das HUD ändert sich nicht.",
    [UI_MENU_UPSCALING_OFF] = "Aus", [UI_MENU_UPSCALING_AUTO] = "Automatisch",
    [UI_MENU_UPSCALING_UNAVAILABLE] = "hier nicht verfügbar",
    [UI_MENU_UPSCALING_UNTIL] = "%s bis zum Neustart",
    [UI_MENU_UPSCALING_QUALITY] = "Leistungsskalierung",
    [UI_MENU_UPSCALING_QUALITY_DESC] = "Größe, in der die 3D-Szene gezeichnet wird, bevor der Upscaler sie auf die "
                                       "Spielauflösung bringt (steht unter dem Wert). Nativ zeichnet sie in voller Größe, "
                                       "am schärfsten (DLAA mit DLSS). Qualität, Ausgewogen, Leistung und Ultra-Leistung "
                                       "zeichnen sie mit etwa 67, 58, 50 und 33 % für mehr FPS; Ultra-Leistung ist für "
                                       "3840 x 2160 gedacht. Gilt nach einem Neustart.",
    [UI_MENU_UPSCALING_NATIVE] = "Aus (volle Auflösung)", [UI_MENU_DLSS_QUALITY] = "Qualität",
    [UI_MENU_DLSS_BALANCED] = "Ausgewogen",
    [UI_MENU_DLSS_PERFORMANCE] = "Leistung", [UI_MENU_UPSCALING_ULTRA] = "Ultra-Leistung",
    [UI_MENU_UPSCALING_MODE_OFF] = "ohne Upscaler",
    [UI_MENU_AA] = "Antialiasing (SMAA)",
    [UI_MENU_AA_DESC] = "SMAA glättet gezackte Kanten, bevor das HUD gezeichnet wird. Hoch ist der Standard; Ultra findet "
                        "mehr Kanten bei etwas mehr GPU-Last. Wird nicht verwendet, solange ein Upscaler arbeitet.",
    [UI_SNAP_SMAA_LOW] = "Niedrig", [UI_SNAP_SMAA_MEDIUM] = "Mittel", [UI_SNAP_SMAA_HIGH] = "Hoch",
    [UI_MENU_AA_OFF] = "Aus",
    [UI_MENU_AA_BY_UPSCALER] = "der Upscaler glättet die Kanten",
    [UI_SNAP_RES] = "Interne Auflösung des Spiels",
    [UI_SNAP_RES_DESC] = "Auflösung, in der die 3D-Szene gezeichnet wird. 100 % sind die spieleigenen 1920 x 1080: "
                         "niedriger für ein sparsameres Bild, höher (Supersampling) für ein schärferes, das GPU-Zeit "
                         "kostet. »Wie der Bildschirm« übernimmt die Höhe des Bildschirms oder Fensters. Funktioniert "
                         "zusammen mit dem Antialiasing. Gilt nach einem Neustart.",
    [UI_SNAP_RES_UPSCALER] = "über 100 %: stelle die Leistungsskalierung auf Aus",
    [UI_SNAP_FG] = "Frame-Generierung",
    [UI_SNAP_FG_DESC] = "AMD-FSR-Frame-Generierung: ein erzeugter Frame zwischen je zwei echten. Die Oberfläche bleibt "
                        "von der Interpolation ausgenommen. Pausiert von selbst, solange das Spiel schneller läuft als "
                        "die halbe Bildwiederholrate des Monitors. Die Leistungsanzeige zeigt die echten und die "
                        "erzeugten FPS. Gilt nach einem Neustart.",
    [UI_SNAP_FG_NEEDS] = "benötigt AMD FSR 3.1 oder FSR 4 als Upscaler",
    [UI_SNAP_HDPH] = "Foto-Miniaturen in HD",
    [UI_SNAP_HDPH_DESC] = "Die Vorschau nach einem Foto und die Fotos in den Ordnern und in der Auswahl nutzen das Foto "
                          "mit 1080 x 720 statt der Miniatur mit 360 x 240 des Spiels. Gespeicherte Fotos und die "
                          "Bewertung ändern sich nicht.",
    [UI_SNAP_SHADOW] = "Schattenauflösung",
    [UI_SNAP_SHADOW_DESC] = "Vergrößert alle Schattenkarten des Spiels. Auto folgt der 3D-Auflösung: 2x bei 1080p, 3x bei "
                            "125-150 %, 4x ab 200 %. In die Kulisse gemalte Schatten ändern sich nicht. Gilt nach einem "
                            "Neustart.",
    [UI_SNAP_TEXPACK] = "HD-Texturenpaket",
    [UI_SNAP_TEXPACK_DESC] = "Verwendet die HD-Texturen aus dem Ordner texpack neben dem Spiel, auf diesem PC aus deinem "
                             "eigenen Spiel erstellt. Gilt nach einem Neustart.",
    [UI_SNAP_TEXPACK_NONE] = "kein Paket im Ordner texpack",
    [UI_SNAP_HDSH] = "HD-Schatten-Modus (experimentell)",
    [UI_SNAP_HDSH_DESC] = "Die Schatten von Pflanzen, Felsen, Treppen und Kulisse sind in Texturen jedes Levels gemalt. "
                          "Ein: Der Launcher liest sie aus deinem eigenen Spiel und vergrößert sie auf diesem PC für "
                          "alle Level (»HD-Schatten erzeugen«; startet von selbst beim Öffnen des Launchers); sichtbar "
                          "sind sie, sobald das fertig ist. Die Echtzeitschatten nutzen dann auch ihre größte Karte "
                          "(aus: sie folgen der internen Auflösung). Gilt nach einem Neustart.",
    [UI_SNAP_TAB] = "Verbesserungen",
    [UI_SNAP_ENH] = "NewSnap-Verbesserungen (ändern die Spiellogik nicht)",
    [UI_SNAP_ASPECT] = "Seitenverhältnis",
    [UI_SNAP_ASPECT_DESC] = "16:9 beibehalten fügt auf breiteren Bildschirmen Balken hinzu; Strecken füllt das Fenster; "
                            "Ultrawide erweitert die 3D-Ansicht mit den Proportionen des Spiels auf das Fenster, lässt "
                            "die Oberfläche in der Mitte und macht die Fotos mit der gewohnten 16:9-Ansicht "
                            "(experimentell).",
    [UI_SNAP_TAB_SYS] = "System",
    [UI_SNAP_SYS_CONT] = "Zurück zum Spiel",
    [UI_SNAP_SYS_CONT_DESC] = "Schließt dieses Menü und setzt das Spiel fort.",
    [UI_SNAP_SYS_RESTART] = "Spiel neu starten",
    [UI_SNAP_SYS_RESTART_DESC] = "Schließt das Spiel und öffnet es erneut, für Einstellungen, die nach einem Neustart "
                                 "gelten. Der Fortschritt seit dem letzten Speichern geht verloren.",
    [UI_SNAP_SYS_QUIT] = "Zum Desktop beenden",
    [UI_SNAP_SYS_QUIT_DESC] = "Schließt das Spiel. Der Fortschritt seit dem letzten Speichern geht verloren; das Spiel "
                              "speichert nur nach jeder Expedition.",
    [UI_MENU_OUTPUT_RES_AUTO] = "Automatisch",
    [UI_MENU_OUTPUT_RES_NEXT] = ", %s nach Neustart",

    [UI_MENU_FPS_LIMIT] = "FPS-Limit",
    [UI_MENU_FPS_LIMIT_DESC] = "Frame-Limit: 30, 60 (Standard), 90, 120 oder 144 FPS, oder VRR (knapp unter der "
                               "Bildwiederholrate des Monitors). Langsamere native Szenen behalten ihr Tempo. Gilt "
                               "sofort; die erreichten FPS hängen von der GPU und dem Anzeigemodus ab.",
    [UI_MENU_FPS_30] = "30 FPS", [UI_MENU_FPS_60] = "60 FPS",
    [UI_MENU_REALTIME] = "Spieltempo nach der Uhr",
    [UI_MENU_REALTIME_DESC] = "Lässt das Spiel nach der Echtzeit ablaufen, damit ein langsamer Frame es nicht bremst.",
    [UI_MENU_CLOTH_REALTIME] = "Stoffe nach der Uhr",
    [UI_MENU_CLOTH_REALTIME_DESC] = "Lässt auch Stoffe und Haare nach der Echtzeit ablaufen.",
    [UI_MENU_HIGHFPS_FIX] = "Korrekturen für hohe FPS",
    [UI_MENU_HIGHFPS_FIX_DESC] = "Korrigiert Physik, die über 30 FPS fehlerhaft ist, und Objekte, die über 60 FPS "
                                 "durchsichtig oder unsichtbar werden.",
    [UI_MENU_GAME_LANG] = "Sprache des Spiels", [UI_MENU_GAME_LANG_DESC] = "Sprache der Texte und Stimmen des Spiels.",
    [UI_MENU_GAME_LANG_AUTO] = "Automatisch",
    [UI_MENU_OPERATION_MODE] = "Konsolenmodus",
    [UI_MENU_OPERATION_MODE_DESC] = "Ob das Spiel glaubt, im Dock (TV) oder im Handheld-Modus zu laufen.",
    [UI_MENU_MODE_DOCKED] = "TV (Dock)", [UI_MENU_MODE_HANDHELD] = "Handheld",
    [UI_MENU_HUD] = "HUD",
    [UI_MENU_HUD_DESC] = "Aus: Das HUD des Spiels wird beim Spielen nicht gezeichnet; die Menüs bleiben. F12 schaltet um.",
    [UI_MENU_ASSUME_FOCUS] = "Ohne Fokus weiterlaufen",
    [UI_MENU_ASSUME_FOCUS_DESC] = "Ein (Standard): Das Spiel läuft weiter, während du in einem anderen Fenster bist, und "
                                  "die Tastatur wirkt erst wieder, wenn das Fenster im Vordergrund ist. Aus: Es pausiert, "
                                  "wenn sein Fenster den Fokus verliert, wie auf der Switch beim Drücken von Home; ein so "
                                  "unterbrochener Ladevorgang kann hängen bleiben.",

    [UI_MENU_MODS_INSTALLED] = "Installierte Mods",
    [UI_MENU_MODS_NONE] = "Noch keine Mods. Entpacke eine Mod in den Ordner mods, ein Ordner pro Mod mit ihrem Ordner "
                          "romfs darin, und starte das Spiel neu.",
    [UI_MENU_MODS_OPEN] = "Mod-Ordner öffnen",
    [UI_MENU_MODS_OPEN_DESC] = "Zeigt den Ordner, aus dem das Spiel die Mods lädt. Er wird angelegt, falls er fehlt.",
    [UI_MENU_MODS_ROW_DESC] = "Ersetzte Spieldateien: %u. Neu hinzugefügte Dateien: %u.",
    [UI_MENU_MODS_OVERRIDDEN] = "%u ihrer Dateien kommen von %s, das weiter oben in der Liste steht.",
    [UI_MENU_MODS_MOVE_HINT] = "Die obere Taste oder Strg+Oben schiebt sie nach oben, die linke Taste oder Strg+Unten "
                               "nach unten. Ändern zwei Mods dieselbe Datei, gewinnt die obere. Änderungen gelten nach "
                               "einem Neustart.",
    [UI_MENU_MODS_EMPTY] = "Dieser Ordner enthält keine romfs-, exefs- oder cheats-Dateien.",
    [UI_MENU_MODS_SUBSDK] = "Diese Mod bringt eigenen Spielcode mit (ein subsdk-Plugin oder ein ersetztes main). Der Port "
                            "kann keine Codemodule laden, daher bleibt die ganze Mod deaktiviert.",
    [UI_MENU_MODS_EXEFS_LATER] = "Diese Mod patcht den Spielcode (exefs). Das Spiel baut die Patches beim nächsten Start "
                                 "ein (ein Neuaufbau von einigen Minuten); bis dahin bleibt die ganze Mod deaktiviert.",
    [UI_MENU_MODS_CHEATS] = "Cheats: %d.",
    [UI_MENU_MODS_CHEATS_FILE] = "Die Cheats dieser Spielversion werden beim Start aus cheats\\%s in dieser Mod gelesen.",
    [UI_MENU_MODS_BAD_NAME] = "Der Ordnername enthält |, das die Mod-Liste zwischen Namen verwendet. Benenne den Ordner "
                              "um.",
    [UI_MENU_MODS_OTHER_VERSION] = "%u ihrer Dateien sind für eine andere Spielversion und werden übersprungen. Suche "
                                   "eine Version dieser Mod, die für deine Spielversion gemacht ist.",
    [UI_MENU_MODS_UNUSED] = "unbenutzt",

    [UI_MENU_VOLUME] = "Lautstärke", [UI_MENU_VOLUME_DESC] = "Gesamtlautstärke des Spiels.",

    [UI_MENU_MOTION] = "Bewegungssteuerung", [UI_MENU_MOTION_DESC] = "Zielen mit dem Gyrosensor des Controllers.",
    [UI_MENU_RUMBLE_STRENGTH] = "Vibrationsstärke",
    [UI_MENU_RUMBLE_STRENGTH_DESC] = "Wie stark der Controller vibriert.",
    [UI_MENU_RUMBLE_CURVE] = "Vibrationskurve",
    [UI_MENU_RUMBLE_CURVE_DESC] = "Niedrigere Werte verstärken schwache Vibrationen.",
    [UI_MENU_RUMBLE_TRIGGERS] = "Trigger-Vibration (Xbox)",
    [UI_MENU_RUMBLE_TRIGGERS_DESC] = "Lässt auch die Trigger eines Xbox-Controllers vibrieren.",
    [UI_MENU_PAD_LAYOUT] = "Tastenanordnung",
    [UI_MENU_PAD_LAYOUT_DESC] = "Welche Taste A ist. Nintendo: die rechte, wie auf der Switch. Xbox: die untere, wie auf "
                                "einem Xbox-Controller. PlayStation: die untere (Kreuz) und die übrigen nach Position, "
                                "für die Mod mit PlayStation-Tasten. »Automatisch« wählt Nintendo für Controller mit "
                                "Nintendo-Beschriftung, PlayStation für PlayStation-Controller und Xbox für alle anderen. "
                                "Welchen Controller die Hinweise des Spiels zeigen, wählst du unter Tastensymbole.",
    [UI_MENU_PAD_LAYOUT_AUTO] = "Automatisch", [UI_MENU_PAD_LAYOUT_NINTENDO] = "Nintendo (A rechts)",
    [UI_MENU_PAD_LAYOUT_XBOX] = "Xbox (A unten)", [UI_MENU_PAD_LAYOUT_PLAYSTATION] = "PlayStation (A unten)",
    [UI_MENU_PAD_LAYOUT_IN_USE] = "aktiv: %s",
    [UI_MENU_PROMPTS] = "Tastensymbole",
    [UI_MENU_PROMPTS_DESC] = "Welche Controller-Tasten die Hinweise des Spiels zeigen. »Automatisch« folgt dem benutzten "
                             "Controller. Nintendo: die des Spiels. Xbox und PlayStation: Tasten-Mods, für die jeweilige "
                             "Anordnung gezeichnet. Das Spiel liest seine Symbole beim Start, sie ändern sich also nach "
                             "einem Neustart.",
    [UI_MENU_PROMPTS_AUTO] = "Automatisch", [UI_MENU_PROMPTS_NINTENDO] = "Nintendo", [UI_MENU_PROMPTS_XBOX] = "Xbox",
    [UI_MENU_PROMPTS_PLAYSTATION] = "PlayStation",
    [UI_MENU_PROMPTS_MISSING] = "Symboldateien fehlen: führe die Installation erneut aus",
    [UI_MENU_PROMPTS_FAILED] = "Symboldateien beschädigt: führe die Installation erneut aus",
    [UI_MENU_PROMPTS_RESTART] = "die Symbole ändern sich nach Neustart",
    [UI_MENU_PROMPTS_OFF_SHAPE] = "aus bei einer Spielauflösung, die nicht 16:9 ist",
    [UI_MENU_PROMPTS_OFF_MODS] = "aus: eine RomFS-Mod ersetzt ihre Dateien",
    [UI_MENU_PROMPTS_OFF_PATCHES] = "aus, solange AC_ROMFS_PATCHES gesetzt ist",
    [UI_MENU_RESTART] = "Jetzt neu starten",
    [UI_MENU_RESTART_DESC] = "Schließt das Spiel und öffnet es erneut mit den neuen Symbolen. Der Fortschritt seit dem "
                             "letzten Speichern geht verloren.",
    [UI_MENU_RESTART_CONFIRM] = "Spiel jetzt neu starten? Der Fortschritt seit dem letzten Speichern geht verloren.",
    [UI_MENU_RESTART_YES] = "Neu starten",
    [UI_MENU_RESTART_SAVING] = "Das Spiel speichert gerade: Du kannst gleich neu starten.",
    [UI_MENU_LSTICK_DEADZONE] = "Totzone des linken Sticks", [UI_MENU_RSTICK_DEADZONE] = "Totzone des rechten Sticks",
    [UI_MENU_STICK_DEADZONE_DESC] = "Wie weit sich ein Stick bewegt, bevor das Spiel es bemerkt. Erhöhe sie, wenn sich "
                                    "die Figur oder die Kamera von selbst bewegt: Lass den Stick los, sieh dir »Stick "
                                    "jetzt« an und stelle die Totzone ein paar Punkte höher ein.",
    [UI_MENU_STICK_DEADZONE_NOW] = "Stick jetzt: %.0f %%",
    [UI_MENU_MOUSE_SENS] = "Mausempfindlichkeit",
    [UI_MENU_MOUSE_SENS_DESC] = "Wie schnell sich die Kamera mit der Maus dreht.",
    [UI_MENU_WALK_KEY] = "Gehen-Taste",
    [UI_MENU_WALK_KEY_DESC] = "Solange du sie hältst, werden die Tastatur-Sticks nur teilweise geneigt, zum Gehen statt "
                              "Rennen. Die Geh-Skala legt fest, wie weit. Wirkt nicht auf Controller oder Maus.",
    [UI_MENU_WALK_KEY_TAKEN] = "auch %s",
    [UI_MENU_WALK_SCALE] = "Geh-Skala",
    [UI_MENU_WALK_SCALE_DESC] = "Neigung der Tastatur-Sticks mit der Gehen-Taste. Die Hälfte ist Gehen, das Maximum ist "
                                "Rennen.",
    [UI_MENU_STICK_SENS] = "Kamerageschwindigkeit per Stick",
    [UI_MENU_STICK_SENS_DESC] = "Multipliziert die Kamerageschwindigkeit des rechten Sticks im Spiel, einschließlich des "
                                "Maximums, in jeder seiner fünf Empfindlichkeiten. Die Maus hat ihre eigene Einstellung.",

    [UI_BINDS_HELP] = "Wähle ein Feld und drücke A oder Eingabe, dann die Taste, Maustaste oder Controller-Taste. Entf "
                      "oder X leert ein Feld. Eine bereits belegte Taste wandert hierher; eine Controller-Taste tauscht "
                      "mit der, die sie ersetzt.",
    [UI_BINDS_COL_KEY1] = "Taste 1", [UI_BINDS_COL_KEY2] = "Taste 2", [UI_BINDS_COL_PAD] = "Controller",
    [UI_BINDS_GROUP_BUTTONS] = "Tasten", [UI_BINDS_GROUP_MOVE] = "Bewegung", [UI_BINDS_GROUP_CAMERA] = "Kamera",
    [UI_BINDS_PRESS_KEY] = "Drücke eine Taste oder Maustaste für %s",
    [UI_BINDS_PRESS_PAD] = "Drücke eine Controller-Taste für %s",
    [UI_BINDS_CANCEL_HINT] = "Esc bricht ab, oder warte %d s",
    [UI_BINDS_TAKEN] = "%s wurde von %s entfernt", [UI_BINDS_SWAPPED] = "%s mit %s getauscht",
    [UI_BINDS_RESET] = "Alle Tasten zurücksetzen",
    [UI_BINDS_RESET_DESC] = "Stellt die Standardtasten wieder her. Die Anordnung oben wird erneut angewendet: Neu belegte "
                            "Controller-Tasten bleiben bis zu diesem Zurücksetzen dort, wo du sie hingelegt hast.",
    [UI_BIND_A] = "A", [UI_BIND_B] = "B", [UI_BIND_X] = "X", [UI_BIND_Y] = "Y",
    [UI_BIND_LCLICK] = "Linken Stick drücken", [UI_BIND_RCLICK] = "Rechten Stick drücken", [UI_BIND_L] = "L",
    [UI_BIND_R] = "R", [UI_BIND_ZL] = "ZL", [UI_BIND_ZR] = "ZR", [UI_BIND_PLUS] = "Plus (+)", [UI_BIND_MINUS] = "Minus (-)",
    [UI_BIND_LEFT] = "Steuerkreuz links", [UI_BIND_UP] = "Steuerkreuz oben", [UI_BIND_RIGHT] = "Steuerkreuz rechts",
    [UI_BIND_DOWN] = "Steuerkreuz unten",
    [UI_BIND_LSTICK_LEFT] = "Nach links bewegen", [UI_BIND_LSTICK_UP] = "Vorwärts bewegen",
    [UI_BIND_LSTICK_RIGHT] = "Nach rechts bewegen", [UI_BIND_LSTICK_DOWN] = "Rückwärts bewegen",
    [UI_BIND_RSTICK_LEFT] = "Kamera nach links", [UI_BIND_RSTICK_UP] = "Kamera nach oben",
    [UI_BIND_RSTICK_RIGHT] = "Kamera nach rechts", [UI_BIND_RSTICK_DOWN] = "Kamera nach unten",
    [UI_BIND_DESC_A] = "Interagieren, aufheben, sprechen.", [UI_BIND_DESC_B] = "Rennen, abbrechen, zurück.",
    [UI_BIND_DESC_X] = "Springen.", [UI_BIND_DESC_Y] = "Angreifen.", [UI_BIND_DESC_LCLICK] = "Ducken.",
    [UI_BIND_DESC_RCLICK] = "Ego-Perspektive.", [UI_BIND_DESC_L] = "Fähigkeiten.",
    [UI_BIND_DESC_R] = "Werfen.", [UI_BIND_DESC_ZL] = "Schild, anvisieren.", [UI_BIND_DESC_ZR] = "Bogen.",
    [UI_BIND_DESC_PLUS] = "Menü, Inventar.", [UI_BIND_DESC_MINUS] = "Karte.",
    [UI_BIND_DESC_DPAD] = "Schnellauswahl.",
    [UI_BIND_DESC_MOVE] = "Bewegt wie der linke Stick. Der linke Stick des Controllers funktioniert immer zusätzlich.",
    [UI_BIND_DESC_CAMERA] = "Dreht die Kamera wie der rechte Stick. Die Maus und der rechte Stick des Controllers "
                            "funktionieren immer zusätzlich.",
    [UI_KEY_SPACE] = "Leertaste", [UI_KEY_TAB] = "Tab", [UI_KEY_LSHIFT] = "Umschalt links", [UI_KEY_LCTRL] = "Strg links",
    [UI_KEY_UP] = "Pfeil oben", [UI_KEY_DOWN] = "Pfeil unten", [UI_KEY_LEFT] = "Pfeil links",
    [UI_KEY_RIGHT] = "Pfeil rechts",
    [UI_KEY_MOUSE_L] = "Linksklick", [UI_KEY_MOUSE_R] = "Rechtsklick", [UI_KEY_MOUSE_M] = "Mittelklick",
    [UI_KEY_MOUSE_X1] = "Maus 4", [UI_KEY_MOUSE_X2] = "Maus 5",
    [UI_KEY_ENTER] = "Eingabe", [UI_KEY_BACKSPACE] = "Rücktaste", [UI_KEY_RSHIFT] = "Umschalt rechts",
    [UI_KEY_RCTRL] = "Strg rechts", [UI_KEY_LALT] = "Alt", [UI_KEY_CAPSLOCK] = "Feststelltaste", [UI_KEY_INSERT] = "Einfg",
    [UI_KEY_DELETE] = "Entf", [UI_KEY_HOME] = "Pos1", [UI_KEY_END] = "Ende", [UI_KEY_PAGEUP] = "Bild auf",
    [UI_KEY_PAGEDOWN] = "Bild ab", [UI_KEY_NUM_FMT] = "Num %s",
    [UI_PAD_SOUTH] = "Untere Taste", [UI_PAD_EAST] = "Rechte Taste", [UI_PAD_WEST] = "Linke Taste",
    [UI_PAD_NORTH] = "Obere Taste", [UI_PAD_LSTICK] = "Linker Stick", [UI_PAD_RSTICK] = "Rechter Stick",
    [UI_PAD_L] = "Linke Schultertaste", [UI_PAD_R] = "Rechte Schultertaste", [UI_PAD_START] = "Start",
    [UI_PAD_BACK] = "Back",
    [UI_PAD_DPAD_LEFT] = "Steuerkreuz links", [UI_PAD_DPAD_UP] = "Steuerkreuz oben", [UI_PAD_DPAD_RIGHT] = "Steuerkreuz rechts",
    [UI_PAD_DPAD_DOWN] = "Steuerkreuz unten", [UI_PAD_ZL] = "Linker Trigger", [UI_PAD_ZR] = "Rechter Trigger",
    [UI_PAD_LPADDLE1] = "Linke Rücktaste", [UI_PAD_RPADDLE1] = "Rechte Rücktaste",
    [UI_PAD_LPADDLE2] = "Linke Rücktaste 2", [UI_PAD_RPADDLE2] = "Rechte Rücktaste 2",
    [UI_PAD_CROSS] = "Kreuz", [UI_PAD_CIRCLE] = "Kreis", [UI_PAD_SQUARE] = "Quadrat", [UI_PAD_TRIANGLE] = "Dreieck",

    [UI_MENU_MENU_LANG] = "Sprache des Menüs",
    [UI_MENU_MENU_LANG_DESC] = "Sprache dieses Menüs und der Bildschirmanzeigen.",
    [UI_MENU_MENU_LANG_AUTO] = "Automatisch (von Windows)",

    [UI_MENU_ADV_WARNING] = "Diese Einstellungen sind für Tests und zur Fehlerbehebung. Ändere sie nur, wenn du weißt, warum.",
    [UI_MENU_GROUP_SCHED] = "Scheduling", [UI_MENU_GROUP_SHADERS] = "Shader und Pipelines",
    [UI_MENU_GROUP_TEXMEM] = "Texturen und Speicher", [UI_MENU_GROUP_FIXES] = "Render-Korrekturen",
    [UI_MENU_GROUP_VULKAN] = "Vulkan", [UI_MENU_GROUP_DIAG] = "Diagnose",
    [UI_MENU_ASYNC_PREEMPT] = "Verdrängung auf virtuellen Kernen",
    [UI_MENU_ASYNC_PREEMPT_DESC] = "Erlaubt einem Spiel-Thread, einen anderen auf demselben virtuellen Kern zu unterbrechen.",
    [UI_MENU_PREEMPT_OFF] = "Aus", [UI_MENU_PREEMPT_ON] = "Ein", [UI_MENU_PREEMPT_INHERIT] = "Nur Vererbung",
    [UI_MENU_REPLAY_ASYNC] = "Frames in eigenem Thread vorbereiten",
    [UI_MENU_REPLAY_ASYNC_DESC] = "Bereitet die Frames für die GPU in einem eigenen Thread statt im Spiel-Thread vor. "
                                  "Fügt bis zu einen Frame Latenz hinzu.",
    [UI_MENU_TIMER_1MS] = "Windows-Timer mit 1 ms",
    [UI_MENU_TIMER_1MS_DESC] = "Erhöht die Auflösung des System-Timers auf 1 ms für gleichmäßigere Framezeiten.",
    [UI_MENU_PIPE_WAIT] = "Umgang mit wartenden Draw-Calls",
    [UI_MENU_PIPE_WAIT_DESC] = "Standard behält das aktuelle Scheduling mit einem reservierten Worker für wartende "
                               "Draw-Calls; Alt (Draw-Call) nutzt das frühere Scheduling.",
    [UI_MENU_PIPE_WAIT_DEFAULT] = "Standard", [UI_MENU_PIPE_WAIT_DRAW] = "Alt (Draw-Call)",
    [UI_MENU_PIPE_SKIP] = "Übersprungene Draw-Calls, während eine Pipeline entsteht",
    [UI_MENU_PIPE_SKIP_DESC] = "Welche Draw-Calls verworfen werden, statt auf ihre Pipeline zu warten.",
    [UI_MENU_PIPE_SKIP_STRICT] = "Streng", [UI_MENU_PIPE_SKIP_ANY] = "Beliebige",
    [UI_MENU_PIPE_SKIP_FULLSCREEN] = "Vollbild-Durchgänge",
    [UI_MENU_LIB_PREBUILD] = "Stage-Bibliotheken vorkompilieren",
    [UI_MENU_LIB_PREBUILD_DESC] = "Kompiliert die Stage-Bibliotheken der Shader vorab im Hintergrund.",
    [UI_MENU_LIB_PREBUILD_THREADS] = "Threads zum Vorkompilieren der Bibliotheken",
    [UI_MENU_LIB_PREBUILD_THREADS_DESC] = "Threads zum Vorkompilieren; »Automatisch« wählt eine Anzahl passend zu deiner CPU.",
    [UI_MENU_PIPE_PREBUILD] = "Pipelines vorkompilieren",
    [UI_MENU_PIPE_PREBUILD_DESC] = "Kompiliert die bekannten Pipelines vorab.",
    [UI_MENU_PREWARM_XLATE] = "Übersetzer vorwärmen",
    [UI_MENU_PREWARM_XLATE_DESC] = "Threads, die die bekannten Shader beim Start übersetzen; »Automatisch« nutzt die "
                                   "Hälfte der CPU-Threads, höchstens 16.",
    [UI_MENU_GPL] = "Grafik-Pipeline-Bibliothek",
    [UI_MENU_GPL_DESC] = "Nutzt die Vulkan-Erweiterung für Pipeline-Bibliotheken; schalte sie aus, wenn dein Treiber "
                         "damit Probleme hat.",
    [UI_MENU_ASTC] = "ASTC-Texturdekodierung",
    [UI_MENU_ASTC_DESC] = "Wo ASTC-komprimierte Texturen dekodiert werden.",
    [UI_MENU_ASTC_AUTO] = "Automatisch", [UI_MENU_ASTC_GPU] = "GPU-Shader", [UI_MENU_ASTC_NATIVE] = "Nativ",
    [UI_MENU_ASTC_CPU] = "CPU",
    [UI_MENU_MEMORY] = "GPU-Speichermodus",
    [UI_MENU_MEMORY_DESC] = "Wie der Speicher des Spiels mit der GPU geteilt wird.",
    [UI_MENU_MEMORY_AUTO] = "Automatisch", [UI_MENU_MEMORY_IMPORT] = "Importieren", [UI_MENU_MEMORY_MIRROR] = "Spiegeln",
    [UI_MENU_MEMORY_VERIFY] = "Prüfen",
    [UI_MENU_TEX_ALIAS] = "Textur-Aliase",
    [UI_MENU_TEX_ALIAS_DESC] = "Eine neue Textur, die über dem Speicher einer noch lebenden angelegt wird, beginnt mit "
                               "deren Inhalt statt leer.",
    [UI_MENU_TEX_VRAM_PRESSURE] = "Limit für Texturspeicher",
    [UI_MENU_TEX_VRAM_PRESSURE_DESC] = "Anteil des Grafikspeichers in Prozent, ab dem vom Spiel freigegebene Texturen "
                                       "verworfen werden (sie kommen vom Datenträger zurück, wenn sie gebraucht werden). "
                                       "0 behält sie.",
    [UI_MENU_ASTC_BC] = "ASTC zu BC komprimieren",
    [UI_MENU_ASTC_BC_DESC] = "Mit dem GPU-Dekodierer: kodiert die dekodierten ASTC-Texturen neu zu BC1, wenn sie "
                             "deckend sind, sonst zu BC3, mit einem Viertel bis einem Achtel des Grafikspeichers. Für "
                             "GPUs mit 4 GB oder weniger; die Texturen wirken etwas blockiger.",
    [UI_MENU_LOD_GUARD] = "LOD-Schutz",
    [UI_MENU_LOD_GUARD_DESC] = "Verhindert, dass Objekte an falscher Stelle aufblitzen oder der ferne Hintergrund einen "
                               "Frame lang flach wird, indem gewartet wird, bis das Spiel die Detailstufen fertig "
                               "umgeschrieben hat, bevor die GPU sie liest.",
    [UI_MENU_FIX_C0] = "Korrektur des Konstantenpuffers",
    [UI_MENU_FIX_C0_DESC] = "Füllt die reservierte Konstantenbank c0 des Treibers (Speichergrößen, Dispatch-Größe, "
                            "Punktgröße, Basisinstanz), statt Nullen zu lesen.",
    [UI_MENU_FIX_ZERO] = "Neuen GPU-Speicher nullen",
    [UI_MENU_FIX_ZERO_DESC] = "Neue GPU-Speicherpools beginnen mit Nullen, wie der Speicher der Switch.",
    [UI_MENU_BIND_SKIP] = "Wiederholte Bindungen überspringen",
    [UI_MENU_BIND_SKIP_DESC] = "Optimierung: überspringt Bindungen, die sich nicht geändert haben.",
    [UI_MENU_SHADER_MEMO] = "Shader-Merkspeicher",
    [UI_MENU_SHADER_MEMO_DESC] = "Optimierung: merkt sich Shader-Suchen.",
    [UI_MENU_PIPE_MEMO] = "Pipeline-Merkspeicher",
    [UI_MENU_PIPE_MEMO_DESC] = "Optimierung: verwendet die Pipeline des vorigen Draw-Calls erneut, wenn sich ihr Zustand "
                               "wiederholt.",
    [UI_MENU_TEX_MEMO] = "Merkspeicher für Texturbindungen",
    [UI_MENU_TEX_MEMO_DESC] = "Optimierung: merkt sich die Textur-Deskriptoren zwischen Draw-Calls.",
    [UI_MENU_DESC_TEMPLATE] = "Deskriptor-Vorlagen",
    [UI_MENU_DESC_TEMPLATE_DESC] = "Optimierung: aktualisiert die Deskriptoren im Block.",
    [UI_MENU_PUSH_SKIP] = "Wiederholte Push Constants überspringen",
    [UI_MENU_PUSH_SKIP_DESC] = "Optimierung: überspringt Push Constants, die sich nicht geändert haben.",
    [UI_MENU_SPLIT_DRAWS] = "Frühes Senden an die GPU",
    [UI_MENU_SPLIT_DRAWS_DESC] = "Sendet die GPU-Arbeit in Teilen, alle N Draw-Calls zwischen Durchgängen, damit die GPU "
                                 "früher anfängt; 0 schaltet es aus.",
    [UI_MENU_VK_VALIDATION] = "Validierungsschicht",
    [UI_MENU_VK_VALIDATION_DESC] = "Prüft jeden Vulkan-Aufruf und bremst das Spiel stark.",
    [UI_MENU_VK_VALIDATION_MISSING] = "Die Validierungsschicht ist nicht installiert.",
    [UI_MENU_VK_DYN_VERTEX] = "Dynamischer Vertex-Zustand",
    [UI_MENU_VK_DYN_VERTEX_DESC] = "Erzwingt die dynamische Vertex-Eingabe ein oder aus; der Standard hängt von der GPU "
                                   "ab.",
    [UI_MENU_VK_DYN_A2C] = "Dynamisches Alpha to Coverage",
    [UI_MENU_VK_DYN_A2C_DESC] = "Erzwingt dynamisches Alpha to Coverage ein oder aus. Standard: aus beim AMD-Treiber für "
                                "RDNA 2 und älter, der damit Figuren schwarz zeichnet; ein bei allen anderen.",
    [UI_MENU_VK_SUBGROUP_PIN] = "Subgroup-Größe festlegen",
    [UI_MENU_VK_SUBGROUP_PIN_DESC] = "Legt die Subgroup-Größe der Shader fest.",
    [UI_MENU_TRACE] = "Leistungsprotokoll", [UI_MENU_TRACE_DESC] = "Schreibt die Framezeiten in eine Datei.",
    [UI_MENU_FLIGHT] = "Flugschreiber",
    [UI_MENU_FLIGHT_DESC] = "Hält einen kurzen Verlauf fest und schreibt ihn, wenn ein Frame hängt.",
    [UI_MENU_FLIGHT_SPIKE_MS] = "Hänger-Schwelle (ms)",
    [UI_MENU_FLIGHT_SPIKE_MS_DESC] = "Framezeit, die als Hänger zählt.",
    [UI_MENU_INPUT_RECORD] = "Eingaben aufzeichnen",
    [UI_MENU_INPUT_RECORD_DESC] = "Schreibt deine Eingaben in eine Datei, um Fehler zu melden.",
    [UI_MENU_OPEN_LOG] = "Protokollordner öffnen", [UI_MENU_OPEN_LOG_DESC] = "Zeigt den Ordner mit den Protokollen.",
    [UI_MENU_COPY_INFO] = "Systeminformationen kopieren",
    [UI_MENU_COPY_INFO_DESC] = "Kopiert GPU, Treiber, CPU, RAM und die geänderten Einstellungen in die Zwischenablage.",
    [UI_MENU_COPY_INFO_DONE] = "Kopiert", [UI_MENU_ACTION_FAILED] = "hat nicht funktioniert",
    [UI_MENU_RESET] = "Alle Einstellungen zurücksetzen", [UI_MENU_RESET_DESC] = "Gilt für alle Reiter.",
    [UI_MENU_RESET_CONFIRM] = "Alle Einstellungen auf ihre Standardwerte zurücksetzen?",
    [UI_MENU_RESET_YES] = "Zurücksetzen",
    [UI_MENU_RESET_NO] = "Abbrechen",

    [UI_MENU_OV_FPS] = "%.0f FPS", [UI_MENU_OV_FRAME_MS] = "%.1f ms", [UI_MENU_OV_GAME_PCT] = "Spiel %.0f%%",
    [UI_MENU_OV_MAX_MS] = "max. %.1f ms",
    [UI_MENU_OV_GPU] = "GPU", [UI_MENU_OV_CPU] = "CPU", [UI_MENU_OV_RAM] = "RAM", [UI_MENU_OV_VRAM] = "VRAM",
    [UI_MENU_OV_TEMP] = "Temperatur", [UI_MENU_OV_POWER] = "Verbrauch", [UI_MENU_OV_CLOCK] = "Takt",
    [UI_MENU_OV_NONE] = "-",
    [UI_MENU_OV_REPLAY] = "Frame-Vorbereitung", [UI_MENU_OV_GPU_TIME] = "GPU-Zeit pro Frame",
    [UI_MENU_OV_PIPE_WAIT] = "Pipeline-Wartezeiten",
    [UI_MENU_OV_SHADER_WAIT] = "Shader-Wartezeiten", [UI_MENU_OV_TEX_UPLOADS] = "Textur-Uploads",
    [UI_MENU_OV_FMT_PCT] = "%.0f%%", [UI_MENU_OV_FMT_TEMP] = "%.0f °C", [UI_MENU_OV_FMT_POWER] = "%.0f W",
    [UI_MENU_OV_FMT_MHZ] = "%.0f MHz", [UI_MENU_OV_FMT_GB] = "%.1f GB", [UI_MENU_OV_FMT_GB_OF] = "/ %.1f GB",
    [UI_MENU_OV_GAME_GB] = "Spiel %.1f GB", [UI_MENU_OV_FMT_MS] = "%.2f ms", [UI_MENU_OV_PER_FRAME] = "%.1f pro Frame",
    [UI_MENU_OV_WINDOW] = "Fenster", [UI_MENU_OV_OUTPUT] = "Spielbild", [UI_MENU_OV_SCENE] = "3D-Szene",
    [UI_MENU_OV_SCALING] = "Skalierung", [UI_MENU_OV_LIMIT] = "FPS-Limit", [UI_MENU_OV_PRESENT] = "Bildausgabe",
    [UI_MENU_OV_TEX] = "Texturkompression", [UI_MENU_OV_OS] = "System",
    [UI_MENU_OV_FMT_SIZE] = "%ux%u", [UI_MENU_OV_FMT_SCENE] = "%ux%u, %.0f%%",
    [UI_MENU_OV_FMT_FSR] = "AMD FSR 1, Schärfe %d%%", [UI_MENU_OV_SCALE_NONE] = "keine (1:1)",
    [UI_MENU_OV_SCALE_BILINEAR] = "bilinear",
    [UI_MENU_OV_FMT_AREA] = "Flächenmittel, Schärfe %d%%",
    [UI_MENU_OV_FMT_PRESHARP] = "RCAS vor dem HUD, Schärfe %d%%",
    [UI_MENU_TAB_CHEATS] = "Cheats",
    [UI_MENU_CHEATS_NONE] = "Keine Cheats für diese Spielversion. Die Cheats einer Mod sind eine Atmosphere-Cheat-Datei "
                            "in ihrem Ordner cheats, benannt nach dem Build des Spiels: mods\\<mod>\\cheats\\%s. "
                            "Starte das Spiel neu, um sie einzulesen. Für Cheats, die den Spielcode ändern, wird das "
                            "Spiel beim Start neu aufgebaut (einige Minuten).",
    [UI_MENU_CHEATS_MOD] = "%s: %d Cheats",
    [UI_MENU_CHEAT_CODE_DESC] = "Ändert den Spielcode. Wirkt sofort.",
    [UI_MENU_CHEAT_KEY_DESC] = "Ändert den Spielcode, solange du %s hältst. Wirkt sofort.",
    [UI_MENU_CHEAT_DATA_DESC] = "Schreibt in jedem Frame in den Speicher des Spiels, solange er aktiviert ist.",
    [UI_MENU_CHEAT_MASTER] = "immer aktiv",
    [UI_MENU_CHEAT_MASTER_DESC] = "Der Mastercode der Datei: Er ist immer aktiv.",
    [UI_MENU_CHEAT_RESTORE] = "nicht nötig",
    [UI_MENU_CHEAT_RESTORE_DESC] = "Schreibt nur den Originalcode des Spiels zurück. Das Deaktivieren eines Cheats tut "
                                   "das bereits.",
    [UI_MENU_CHEAT_REBUILD] = "nach dem Neuaufbau",
    [UI_MENU_CHEAT_REBUILD_DESC] = "Dieser Cheat ändert den Spielcode und ist neu oder wurde bearbeitet, seit das Spiel "
                                   "gebaut wurde. Das Spiel baut ihn beim nächsten Start ein (einige Minuten), oder "
                                   "nutze Spiel jetzt neu aufbauen.",
    [UI_MENU_CHEAT_UNSUPPORTED] = "nicht unterstützt",
    [UI_MENU_CHEAT_UNSUPPORTED_DESC] = "Dieser Cheat kann mit dieser Spielversion nicht verwendet werden:",
    [UI_MENU_CHEATS_REBUILD] = "Spiel jetzt neu aufbauen",
    [UI_MENU_CHEATS_REBUILD_DESC] = "Einige Cheats ändern den Spielcode und sind nicht eingebaut: Sie sind neu oder "
                                    "wurden bearbeitet, oder ihr letzter Neuaufbau ist fehlgeschlagen oder wurde "
                                    "abgebrochen. Schließt das Spiel; die Installation baut sie ein (einige Minuten) und "
                                    "öffnet das Spiel wieder. Der Fortschritt seit dem letzten Speichern geht verloren.",
    [UI_MENU_MODS_EXEFS_UNSUPPORTED] = "Diese Mod patcht den Spielcode (exefs) auf eine Weise, die der Port nicht "
                                       "anwenden kann, daher bleibt die ganze Mod deaktiviert. %s",
    [UI_MENU_MODS_EXEFS_OTHER] = "Ihre Code-Patches (exefs) sind für eine andere Spielversion.",
    [UI_MENU_MODS_EXEFS_ON] = "Code-Patches aktiv: %d Dateien.",
    [UI_MENU_MODS_REPLACES_BUILTIN] = "Code-Patches aktiv: %d Dateien. Sie ersetzen den eigenen Patch %s des Ports, der "
                                      "deaktiviert bleibt, solange diese Mod aktiviert ist.",
};
