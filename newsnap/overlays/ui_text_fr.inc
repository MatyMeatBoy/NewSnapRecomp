// The in-game menu in French (MENU-LANG-01), every string of text_es (ui_text_es.inc).
// Included by ui_text.c in place of the keyboard-only French row.
static const char *const text_fr[UI_TEXT_COUNT] = {
    SWKBD("Saisie de texte", "Entrez un nom", "Cheval", "OK", "Annuler", "Manette : A = OK, B = Annuler"),

    [UI_MENU_TITLE] = "Paramètres",
    [UI_MENU_TAB_SCREEN] = "Écran", [UI_MENU_TAB_GAME] = "Jeu", [UI_MENU_TAB_MODS] = "Mods",
    [UI_MENU_TAB_SOUND] = "Son",
    [UI_MENU_TAB_CONTROLS] = "Commandes", [UI_MENU_TAB_MENU] = "Menu", [UI_MENU_TAB_ADVANCED] = "Avancé",
    [UI_MENU_CONTINUE] = "Continuer", [UI_MENU_QUIT] = "Quitter le jeu",
    [UI_MENU_ON] = "Activé", [UI_MENU_OFF] = "Désactivé", [UI_MENU_AUTO] = "Automatique",
    [UI_MENU_DEFAULT_MARK] = "par défaut",
    [UI_MENU_AFTER_RESTART] = "après redémarrage", [UI_MENU_SET_BY_ENV] = "fixé par une variable d'environnement",
    [UI_MENU_SAVE_FAILED] = "impossible d'enregistrer les paramètres",
    [UI_MENU_VERSION] = "NewSnapRecomp %s, Snap %s",

    [UI_MENU_FULLSCREEN] = "Plein écran",
    [UI_MENU_FULLSCREEN_DESC] = "Le jeu occupe tout l'écran ; F11 bascule ce mode.",
    [UI_MENU_WINDOW_SIZE] = "Taille de la fenêtre",
    [UI_MENU_WINDOW_SIZE_DESC] = "Taille de la fenêtre du jeu hors du plein écran.",
    [UI_MENU_WINDOW_SIZE_CUSTOM] = "Personnalisée",
    [UI_MENU_PRESENT] = "Présentation", [UI_MENU_PRESENT_DESC] = "Comment les images terminées arrivent à l'écran.",
    [UI_MENU_PRESENT_MAILBOX] = "Mailbox", [UI_MENU_PRESENT_VSYNC] = "VSync", [UI_MENU_PRESENT_IMMEDIATE] = "Immédiate",
    [UI_MENU_PRESENT_IN_USE] = "utilisé : %s",
    [UI_MENU_GPU] = "Carte graphique", [UI_MENU_GPU_DESC] = "Le périphérique Vulkan qui dessine le jeu.",
    [UI_MENU_GPU_AUTO] = "Automatique",
    [UI_MENU_PERF_OVERLAY] = "Informations de performance",
    [UI_MENU_PERF_OVERLAY_DESC] = "FPS dans le coin supérieur droit. « Complètes » ajoute les temps d'image avec un "
                                  "graphique, la charge du CPU, du GPU et de la mémoire, les températures et les "
                                  "attentes du thread de rendu. F10 change de mode.",
    [UI_MENU_PERF_OFF] = "Masquées", [UI_MENU_PERF_FPS] = "FPS", [UI_MENU_PERF_FULL] = "Complètes",
    [UI_PERF_LINE_FPS] = "%.0f fps",
    [UI_MENU_GRAPHICS] = "Image",
    [UI_MENU_OUTPUT_RES] = "Résolution du jeu",
    [UI_MENU_OUTPUT_RES_DESC] = "Taille à laquelle le jeu dessine son image et son interface. 1280 x 720 est la plus "
                                "légère, pour les GPU modestes. Au-dessus de 1920 x 1080, le jeu demande plus de "
                                "mémoire (environ 240 Mo de plus en 2560 x 1440, 790 Mo en 3840 x 2160) et de temps "
                                "GPU. S'applique après redémarrage. « Automatique » prend la taille de l'écran : "
                                "jusqu'à 1920 x 1080, et jusqu'à 3840 x 2160 avec un upscaler actif.",
    [UI_MENU_UPSCALER] = "Mise à l'échelle vers la fenêtre",
    [UI_MENU_UPSCALER_DESC] = "Comment l'image est mise à l'échelle de la fenêtre. FSR conserve des contours et des "
                              "détails plus nets que le bilinéaire, et accentue l'image même si elle tient déjà dans "
                              "la fenêtre.",
    [UI_MENU_UPSCALER_FSR] = "AMD FSR 1", [UI_MENU_UPSCALER_BILINEAR] = "Bilinéaire",
    [UI_MENU_FOV] = "Champ de vision",
    [UI_MENU_FOV_DESC] = "Part du monde que montre la caméra, en pourcentage de celui du jeu (50 degrés à la "
                         "verticale en jeu). Les cinématiques conservent le cadrage du jeu.",
    [UI_MENU_ANISO] = "Filtrage des textures",
    [UI_MENU_ANISO_DESC] = "Filtrage anisotrope : le sol, les chemins et les murs vus de biais restent nets au loin "
                           "au lieu de devenir flous. Jeu : le niveau demandé par le jeu, comme sur Switch. Auto : "
                           "16x avec une échelle 3D de 1440p, le double du niveau du jeu en 2160p et celui du jeu "
                           "dans les autres cas.",
    [UI_MENU_ANISO_GAME] = "Jeu",
    [UI_MENU_ANISO_AUTO] = "Auto",
    [UI_MENU_SHARPNESS] = "Netteté de FSR",
    [UI_MENU_SHARPNESS_DESC] = "Accentuation après la mise à l'échelle FSR ; 0 la désactive.",
    [UI_MENU_COLOR] = "Couleur",
    [UI_MENU_COLOR_PRESET] = "Profil de couleur",
    [UI_MENU_COLOR_PRESET_DESC] = "Règle les quatre valeurs ci-dessous. Vif : plus de contraste et de saturation, et "
                                  "des ombres un peu plus ouvertes (pensé pour l'OLED). Clarté : un peu plus de "
                                  "contraste, de saturation et de luminosité. Modifier une valeur fait passer le "
                                  "profil sur Personnalisé. Le HUD change avec l'image ; ce menu, non.",
    [UI_MENU_COLOR_DEFAULT] = "Celui du jeu", [UI_MENU_COLOR_VIVID] = "Vif (OLED)", [UI_MENU_COLOR_CLARITY] = "Clarté",
    [UI_MENU_COLOR_CUSTOM] = "Personnalisé",
    [UI_MENU_COLOR_BRIGHTNESS] = "Luminosité",
    [UI_MENU_COLOR_BRIGHTNESS_DESC] = "S'ajoute à chaque couleur ; 0 ne change rien.",
    [UI_MENU_COLOR_CONTRAST] = "Contraste",
    [UI_MENU_COLOR_CONTRAST_DESC] = "Éloigne les couleurs du gris moyen (plus de 100 %) ou les en rapproche ; 100 % ne "
                                    "change rien.",
    [UI_MENU_COLOR_SATURATION] = "Saturation",
    [UI_MENU_COLOR_SATURATION_DESC] = "Intensité de la couleur par rapport au gris ; 100 % ne change rien.",
    [UI_MENU_COLOR_GAMMA] = "Gamma",
    [UI_MENU_COLOR_GAMMA_DESC] = "En dessous de 1, éclaircit les tons sombres et moyens ; au-dessus, les assombrit ; "
                                 "1 ne change rien.",
    [UI_MENU_HDR_GROUP] = "HDR",
    [UI_MENU_HDR] = "Sortie HDR",
    [UI_MENU_HDR_DESC] = "Hautes lumières intenses sur un écran HDR. Nécessite le HDR activé dans Windows (« Utiliser "
                         "le HDR ») ou un compositeur Wayland avec gestion des couleurs ; sans cela, l'image reste en "
                         "SDR. S'applique après redémarrage. Le profil de couleur ci-dessus est destiné au SDR et "
                         "n'est pas utilisé en HDR.",
    [UI_MENU_HDR_PEAK] = "Luminosité maximale",
    [UI_MENU_HDR_PEAK_DESC] = "Le maximum de votre écran en nits ; les hautes lumières les plus intenses s'y arrêtent.",
    [UI_MENU_HDR_GAME] = "Luminosité du jeu",
    [UI_MENU_HDR_GAME_DESC] = "Nits du blanc de l'image (blanc papier). 203 est la référence HDR ; augmentez-la dans "
                              "une pièce lumineuse.",
    [UI_MENU_HDR_UI] = "Luminosité du HUD et du menu",
    [UI_MENU_HDR_UI_DESC] = "Nits du blanc du HUD et de ce menu.",
    [UI_MENU_HDR_HUE] = "Correction de teinte des hautes lumières",
    [UI_MENU_HDR_HUE_DESC] = "Les couleurs intenses, comme le feu ou les étincelles, tendent vers le blanc comme dans "
                             "l'image SDR du jeu, de même que la lumière qu'elles projettent ; 0 les laisse "
                             "entièrement saturées.",
    [UI_MENU_SHADOW_SCALE] = "Résolution des ombres",
    [UI_MENU_SHADOW_SCALE_DESC] = "Dessine la carte d'ombres du soleil autant de fois plus grande par côté que le "
                                  "2048x2048 du jeu : bords d'ombre et ombres de feuillage plus nets, au prix de "
                                  "mémoire vidéo (environ 85 à 130 Mio en 2x, 340 à 520 Mio en 4x). S'applique au "
                                  "prochain démarrage.",
    [UI_MENU_AO] = "Occlusion ambiante",
    [UI_MENU_AO_DESC] = "Assombrit les plis, les coins et le sol sous les personnages et les objets, là où arrive peu "
                        "de lumière ambiante. Elle est calculée à l'écran après l'éclairage du monde ; le jeu n'a pas "
                        "la sienne. « Élevée » coûte plus de temps GPU que « Basse ». S'applique immédiatement.",
    [UI_MENU_AO_OFF] = "Désactivée",
    [UI_MENU_AO_LOW] = "Basse",
    [UI_MENU_AO_HIGH] = "Élevée",
    [UI_MENU_UPSCALING] = "Upscaler (FSR / DLSS)",
    [UI_MENU_UPSCALING_DESC] = "Un upscaler temporel à la place de l'anticrénelage du jeu : des contours plus doux et "
                               "moins de scintillement, et plus de FPS avec un mode inférieur à Natif. NVIDIA DLSS "
                               "nécessite un GPU NVIDIA RTX et nvngx_dlss.dll à côté de newsnap.exe ; Intel XeSS, un "
                               "GPU récent et libxess.dll à côté de newsnap.exe ; AMD FSR fonctionne sur n'importe "
                               "quel GPU. « Automatique » utilise DLSS là où c'est possible et FSR dans les autres "
                               "cas. DLSS et XeSS choisis ici s'appliquent après redémarrage. Le HUD ne change pas.",
    [UI_MENU_UPSCALING_DESC_OTHER] = "Un upscaler temporel à la place de l'anticrénelage du jeu : des contours plus "
                                     "doux et moins de scintillement, et plus de FPS avec un mode inférieur à Natif. "
                                     "AMD FSR fonctionne sur n'importe quel GPU ; ici, « Automatique » correspond à "
                                     "FSR (NVIDIA DLSS et Intel XeSS sont réservés à Windows). Le HUD ne change pas.",
    [UI_MENU_UPSCALING_OFF] = "Désactivé", [UI_MENU_UPSCALING_AUTO] = "Automatique",
    [UI_MENU_UPSCALING_UNAVAILABLE] = "non disponible ici",
    [UI_MENU_UPSCALING_UNTIL] = "%s jusqu'au redémarrage",
    [UI_MENU_UPSCALING_QUALITY] = "Mise à l'échelle de performance",
    [UI_MENU_UPSCALING_QUALITY_DESC] = "Taille à laquelle la scène 3D est dessinée avant que l'upscaler ne l'amène à "
                                       "la résolution du jeu (affichée sous la valeur). Natif la dessine en taille "
                                       "réelle, la plus nette (DLAA avec DLSS). Qualité, Équilibré, Performance et "
                                       "Ultra performance la dessinent à environ 67, 58, 50 et 33 % pour plus de FPS "
                                       "; Ultra performance est prévu pour le 3840 x 2160. S'applique après "
                                       "redémarrage.",
    [UI_MENU_UPSCALING_NATIVE] = "Désactivé (résolution complète)", [UI_MENU_DLSS_QUALITY] = "Qualité",
    [UI_MENU_DLSS_BALANCED] = "Équilibré",
    [UI_MENU_DLSS_PERFORMANCE] = "Performance", [UI_MENU_UPSCALING_ULTRA] = "Ultra performance",
    [UI_MENU_UPSCALING_MODE_OFF] = "sans upscaler",
    [UI_MENU_AA] = "Anticrénelage (SMAA)",
    [UI_MENU_AA_DESC] = "SMAA adoucit les contours crénelés avant le dessin du HUD. Élevé est la valeur par défaut ; "
                        "Ultra détecte plus de contours pour un peu plus de GPU. Il n'est pas utilisé tant qu'un "
                        "upscaler fonctionne.",
    [UI_SNAP_SMAA_LOW] = "Bas", [UI_SNAP_SMAA_MEDIUM] = "Moyen", [UI_SNAP_SMAA_HIGH] = "Élevé",
    [UI_MENU_AA_OFF] = "Désactivé",
    [UI_MENU_AA_BY_UPSCALER] = "l'upscaler adoucit les contours",
    [UI_SNAP_RES] = "Résolution interne du jeu",
    [UI_SNAP_RES_DESC] = "Résolution à laquelle la scène 3D est dessinée. 100 % correspond au 1920 x 1080 propre au "
                         "jeu : baissez-la pour une image plus légère, augmentez-la (supersampling) pour une image "
                         "plus nette qui coûte du temps GPU. « Selon l'écran » reprend la hauteur de l'écran ou de la "
                         "fenêtre. Fonctionne avec l'anticrénelage. S'applique après redémarrage.",
    [UI_SNAP_RES_UPSCALER] = "au-dessus de 100 % : réglez la mise à l'échelle de performance sur Désactivé",
    [UI_SNAP_FG] = "Génération d'images",
    [UI_SNAP_FG_DESC] = "Génération d'images AMD FSR : une image générée entre deux images réelles. L'interface reste "
                        "hors de l'interpolation. Elle se met en pause d'elle-même tant que le jeu tourne plus vite "
                        "que la moitié du taux de rafraîchissement de l'écran. Les informations de performance "
                        "affichent les FPS réels et générés. S'applique après redémarrage.",
    [UI_SNAP_FG_NEEDS] = "nécessite AMD FSR 3.1 ou FSR 4 comme upscaler",
    [UI_SNAP_HDPH] = "Miniatures des photos en HD",
    [UI_SNAP_HDPH_DESC] = "L'aperçu après une photo et les photos des dossiers et de la sélection utilisent la photo "
                          "en 1080 x 720 au lieu de la miniature en 360 x 240 du jeu. Les photos enregistrées et le "
                          "score ne changent pas.",
    [UI_SNAP_SHADOW] = "Résolution des ombres",
    [UI_SNAP_SHADOW_DESC] = "Agrandit toutes les cartes d'ombres du jeu. Auto suit la résolution 3D : 2x en 1080p, 3x "
                            "à 125-150 %, 4x à partir de 200 %. Les ombres peintes dans le décor ne changent pas. "
                            "S'applique après redémarrage.",
    [UI_SNAP_TEXPACK] = "Pack de textures HD",
    [UI_SNAP_TEXPACK_DESC] = "Utilise les textures HD du dossier texpack à côté du jeu, créées sur ce PC à partir de "
                             "votre propre jeu. S'applique après redémarrage.",
    [UI_SNAP_TEXPACK_NONE] = "aucun pack dans le dossier texpack",
    [UI_SNAP_HDSH] = "Mode Ombres HD (expérimental)",
    [UI_SNAP_HDSH_DESC] = "Les ombres des plantes, des rochers, des escaliers et du décor sont peintes dans des "
                          "textures propres à chaque niveau. Activé : le launcher les lit dans votre propre jeu et "
                          "les agrandit sur ce PC pour tous les niveaux (« Générer les ombres HD » ; démarre "
                          "automatiquement à l'ouverture du launcher) ; elles sont visibles une fois l'opération "
                          "terminée. Les ombres en temps réel passent aussi à leur carte la plus grande (désactivé, "
                          "elles suivent la résolution interne). S'applique après redémarrage.",
    [UI_SNAP_TAB] = "Améliorations",
    [UI_SNAP_ENH] = "Améliorations de NewSnap (elles ne changent pas la logique du jeu)",
    [UI_SNAP_ASPECT] = "Format d'image",
    [UI_SNAP_ASPECT_DESC] = "Conserver 16:9 ajoute des bandes sur les écrans plus larges ; Étirer remplit la fenêtre ; "
                            "Ultrawide étend la vue 3D à la fenêtre avec les proportions du jeu, laisse l'interface au "
                            "centre et prend les photos avec la vue 16:9 habituelle (expérimental).",
    [UI_SNAP_TAB_SYS] = "Système",
    [UI_SNAP_SYS_CONT] = "Retourner au jeu",
    [UI_SNAP_SYS_CONT_DESC] = "Ferme ce menu et reprend la partie.",
    [UI_SNAP_SYS_RESTART] = "Redémarrer le jeu",
    [UI_SNAP_SYS_RESTART_DESC] = "Ferme le jeu et le rouvre, pour les paramètres qui s'appliquent après redémarrage. "
                                 "La progression depuis votre dernière sauvegarde est perdue.",
    [UI_SNAP_SYS_QUIT] = "Quitter vers le bureau",
    [UI_SNAP_SYS_QUIT_DESC] = "Ferme le jeu. La progression depuis votre dernière sauvegarde est perdue ; le jeu ne "
                              "sauvegarde automatiquement qu'après chaque expédition.",
    [UI_MENU_OUTPUT_RES_AUTO] = "Automatique",
    [UI_MENU_OUTPUT_RES_NEXT] = ", %s après redémarrage",

    [UI_MENU_FPS_LIMIT] = "Limite de FPS",
    [UI_MENU_FPS_LIMIT_DESC] = "Limite d'images par seconde : 30, 60 (par défaut), 90, 120 ou 144 FPS, ou VRR (juste "
                               "en dessous du taux de rafraîchissement de l'écran). Les scènes natives plus lentes "
                               "conservent leur rythme. S'applique immédiatement ; les FPS atteints dépendent du GPU "
                               "et du mode d'affichage.",
    [UI_MENU_FPS_30] = "30 FPS", [UI_MENU_FPS_60] = "60 FPS",
    [UI_MENU_REALTIME] = "Vitesse du jeu selon l'horloge",
    [UI_MENU_REALTIME_DESC] = "Fait avancer le jeu selon le temps réel, pour qu'une image lente ne le ralentisse pas.",
    [UI_MENU_CLOTH_REALTIME] = "Tissus selon l'horloge",
    [UI_MENU_CLOTH_REALTIME_DESC] = "Fait aussi avancer les tissus et les cheveux selon le temps réel.",
    [UI_MENU_HIGHFPS_FIX] = "Corrections pour FPS élevés",
    [UI_MENU_HIGHFPS_FIX_DESC] = "Corrige la physique qui se dérègle au-dessus de 30 FPS et les objets qui deviennent "
                                 "transparents ou invisibles au-dessus de 60.",
    [UI_MENU_GAME_LANG] = "Langue du jeu", [UI_MENU_GAME_LANG_DESC] = "Langue des textes et des voix du jeu.",
    [UI_MENU_GAME_LANG_AUTO] = "Automatique",
    [UI_MENU_OPERATION_MODE] = "Mode de la console",
    [UI_MENU_OPERATION_MODE_DESC] = "Si le jeu se croit sur la station d'accueil (TV) ou en mode portable.",
    [UI_MENU_MODE_DOCKED] = "TV (station d'accueil)", [UI_MENU_MODE_HANDHELD] = "Portable",
    [UI_MENU_HUD] = "HUD",
    [UI_MENU_HUD_DESC] = "Désactivé, le HUD du jeu n'est pas dessiné en jeu ; les menus restent. F12 bascule ce "
                         "réglage.",
    [UI_MENU_ASSUME_FOCUS] = "Continuer sans le focus",
    [UI_MENU_ASSUME_FOCUS_DESC] = "Activé (par défaut), le jeu continue pendant que vous êtes dans une autre fenêtre "
                                  "et le clavier n'agit pas tant que la fenêtre n'est pas revenue au premier plan. "
                                  "Désactivé, il se met en pause quand sa fenêtre perd le focus, comme sur Switch en "
                                  "appuyant sur HOME ; un chargement interrompu ainsi peut rester bloqué.",

    [UI_MENU_MODS_INSTALLED] = "Mods installés",
    [UI_MENU_MODS_NONE] = "Aucun mod pour l'instant. Décompressez un mod dans le dossier mods, un dossier par mod "
                          "avec son dossier romfs à l'intérieur, puis redémarrez le jeu.",
    [UI_MENU_MODS_OPEN] = "Ouvrir le dossier des mods",
    [UI_MENU_MODS_OPEN_DESC] = "Affiche le dossier depuis lequel le jeu charge les mods. Il est créé s'il n'existe "
                               "pas.",
    [UI_MENU_MODS_ROW_DESC] = "Fichiers du jeu remplacés : %u. Nouveaux fichiers ajoutés : %u.",
    [UI_MENU_MODS_OVERRIDDEN] = "%u de ses fichiers viennent de %s, placé plus haut dans la liste.",
    [UI_MENU_MODS_MOVE_HINT] = "Le bouton du haut ou Ctrl+Haut le monte, le bouton de gauche ou Ctrl+Bas le descend. "
                               "Quand deux mods modifient le même fichier, celui placé le plus haut l'emporte. Les "
                               "changements s'appliquent après redémarrage.",
    [UI_MENU_MODS_EMPTY] = "Ce dossier ne contient aucun fichier romfs, exefs ni cheats.",
    [UI_MENU_MODS_SUBSDK] = "Ce mod apporte son propre code de jeu (un plugin subsdk ou un main remplacé). Le portage "
                            "ne peut pas charger de modules de code, le mod entier est donc désactivé.",
    [UI_MENU_MODS_EXEFS_LATER] = "Ce mod patche le code du jeu (exefs). Le jeu intègre les patchs au prochain "
                                 "démarrage (une reconstruction de quelques minutes) ; d'ici là, le mod entier est "
                                 "désactivé.",
    [UI_MENU_MODS_CHEATS] = "Codes de triche : %d.",
    [UI_MENU_MODS_CHEATS_FILE] = "Les codes de triche de cette version du jeu sont lus au démarrage depuis cheats\\%s "
                                 "dans ce mod.",
    [UI_MENU_MODS_BAD_NAME] = "Le nom du dossier contient |, que la liste des mods utilise entre les noms. Renommez le "
                              "dossier.",
    [UI_MENU_MODS_OTHER_VERSION] = "%u de ses fichiers sont destinés à une autre version du jeu et sont ignorés. "
                                   "Cherchez une version de ce mod faite pour votre version du jeu.",
    [UI_MENU_MODS_UNUSED] = "inutilisé",

    [UI_MENU_VOLUME] = "Volume", [UI_MENU_VOLUME_DESC] = "Volume général du jeu.",

    [UI_MENU_MOTION] = "Commandes par mouvements", [UI_MENU_MOTION_DESC] = "Viser avec le gyroscope de la manette.",
    [UI_MENU_RUMBLE_STRENGTH] = "Intensité des vibrations",
    [UI_MENU_RUMBLE_STRENGTH_DESC] = "Force avec laquelle la manette vibre.",
    [UI_MENU_RUMBLE_CURVE] = "Courbe des vibrations",
    [UI_MENU_RUMBLE_CURVE_DESC] = "Des valeurs plus basses renforcent les vibrations légères.",
    [UI_MENU_RUMBLE_TRIGGERS] = "Vibration des gâchettes (Xbox)",
    [UI_MENU_RUMBLE_TRIGGERS_DESC] = "Fait aussi vibrer les gâchettes d'une manette Xbox.",
    [UI_MENU_PAD_LAYOUT] = "Disposition des boutons",
    [UI_MENU_PAD_LAYOUT_DESC] = "Quel bouton est A. Nintendo : celui de droite, comme sur Switch. Xbox : celui du "
                                "bas, comme sur une manette Xbox. PlayStation : celui du bas (croix) et les autres "
                                "selon leur position, pour le mod de boutons PlayStation. « Automatique » choisit "
                                "Nintendo pour les manettes aux inscriptions Nintendo, PlayStation pour les manettes "
                                "PlayStation et Xbox pour les autres. La manette affichée par les icônes du jeu se "
                                "choisit dans Icônes de boutons.",
    [UI_MENU_PAD_LAYOUT_AUTO] = "Automatique", [UI_MENU_PAD_LAYOUT_NINTENDO] = "Nintendo (A à droite)",
    [UI_MENU_PAD_LAYOUT_XBOX] = "Xbox (A en bas)", [UI_MENU_PAD_LAYOUT_PLAYSTATION] = "PlayStation (A en bas)",
    [UI_MENU_PAD_LAYOUT_IN_USE] = "utilisée : %s",
    [UI_MENU_PROMPTS] = "Icônes de boutons",
    [UI_MENU_PROMPTS_DESC] = "Quels boutons de manette affichent les icônes du jeu. « Automatique » suit la manette "
                             "utilisée. Nintendo : celles du jeu. Xbox et PlayStation : des mods de boutons dessinés "
                             "pour chaque disposition. Le jeu lit ses icônes au démarrage, elles changent donc après "
                             "redémarrage.",
    [UI_MENU_PROMPTS_AUTO] = "Automatique", [UI_MENU_PROMPTS_NINTENDO] = "Nintendo", [UI_MENU_PROMPTS_XBOX] = "Xbox",
    [UI_MENU_PROMPTS_PLAYSTATION] = "PlayStation",
    [UI_MENU_PROMPTS_MISSING] = "fichiers d'icônes manquants : relancez l'installation",
    [UI_MENU_PROMPTS_FAILED] = "fichiers d'icônes endommagés : relancez l'installation",
    [UI_MENU_PROMPTS_RESTART] = "les icônes changent après redémarrage",
    [UI_MENU_PROMPTS_OFF_SHAPE] = "désactivé avec une résolution du jeu qui n'est pas en 16:9",
    [UI_MENU_PROMPTS_OFF_MODS] = "désactivé : un mod RomFS remplace ses fichiers",
    [UI_MENU_PROMPTS_OFF_PATCHES] = "désactivé tant que AC_ROMFS_PATCHES est défini",
    [UI_MENU_RESTART] = "Redémarrer maintenant",
    [UI_MENU_RESTART_DESC] = "Ferme le jeu et le rouvre avec les nouvelles icônes. La progression depuis votre "
                             "dernière sauvegarde est perdue.",
    [UI_MENU_RESTART_CONFIRM] = "Redémarrer le jeu maintenant ? La progression depuis votre dernière sauvegarde est "
                                "perdue.",
    [UI_MENU_RESTART_YES] = "Redémarrer",
    [UI_MENU_RESTART_SAVING] = "Le jeu est en train de sauvegarder : vous pourrez redémarrer dans un instant.",
    [UI_MENU_LSTICK_DEADZONE] = "Zone morte du stick gauche", [UI_MENU_RSTICK_DEADZONE] = "Zone morte du stick droit",
    [UI_MENU_STICK_DEADZONE_DESC] = "De combien un stick doit bouger avant que le jeu le remarque. Augmentez-la si le "
                                    "personnage ou la caméra bougent tout seuls : relâchez le stick, regardez « stick "
                                    "actuel » et réglez la zone morte quelques points au-dessus.",
    [UI_MENU_STICK_DEADZONE_NOW] = "stick actuel : %.0f %%",
    [UI_MENU_MOUSE_SENS] = "Sensibilité de la souris",
    [UI_MENU_MOUSE_SENS_DESC] = "Vitesse à laquelle la caméra tourne avec la souris.",
    [UI_MENU_WALK_KEY] = "Touche de marche",
    [UI_MENU_WALK_KEY_DESC] = "Tant qu'elle est maintenue, les sticks du clavier ne s'inclinent qu'en partie, pour "
                              "marcher au lieu de courir. L'échelle de marche fixe de combien. N'affecte ni la "
                              "manette ni la souris.",
    [UI_MENU_WALK_KEY_TAKEN] = "aussi %s",
    [UI_MENU_WALK_SCALE] = "Échelle de marche",
    [UI_MENU_WALK_SCALE_DESC] = "Inclinaison des sticks du clavier avec la touche de marche. La moitié correspond à la "
                                "marche, le maximum à la course.",
    [UI_MENU_STICK_SENS] = "Vitesse de la caméra au stick",
    [UI_MENU_STICK_SENS_DESC] = "Multiplie la vitesse de caméra du stick droit du jeu, maximum compris, pour chacune "
                                "de ses cinq sensibilités. La souris a son propre réglage.",

    [UI_BINDS_HELP] = "Choisissez une case et appuyez sur A ou Entrée, puis sur la touche, le bouton de la souris ou "
                      "le bouton de la manette. Suppr ou X vide une case. Une touche déjà utilisée est déplacée ici ; "
                      "un bouton de la manette est échangé avec celui qu'il remplace.",
    [UI_BINDS_COL_KEY1] = "Touche 1", [UI_BINDS_COL_KEY2] = "Touche 2", [UI_BINDS_COL_PAD] = "Manette",
    [UI_BINDS_GROUP_BUTTONS] = "Boutons", [UI_BINDS_GROUP_MOVE] = "Déplacement", [UI_BINDS_GROUP_CAMERA] = "Caméra",
    [UI_BINDS_PRESS_KEY] = "Appuyez sur une touche ou un bouton de la souris pour %s",
    [UI_BINDS_PRESS_PAD] = "Appuyez sur un bouton de la manette pour %s",
    [UI_BINDS_CANCEL_HINT] = "Esc annule, ou attendez %d s",
    [UI_BINDS_TAKEN] = "%s a été retiré de %s", [UI_BINDS_SWAPPED] = "%s échangé avec %s",
    [UI_BINDS_RESET] = "Réinitialiser tous les boutons",
    [UI_BINDS_RESET_DESC] = "Rétablit les touches et les boutons par défaut. La disposition ci-dessus s'applique de "
                            "nouveau : les boutons de la manette réassignés restent où vous les avez placés jusqu'à "
                            "cette réinitialisation.",
    [UI_BIND_A] = "A", [UI_BIND_B] = "B", [UI_BIND_X] = "X", [UI_BIND_Y] = "Y",
    [UI_BIND_LCLICK] = "Appui sur le stick gauche", [UI_BIND_RCLICK] = "Appui sur le stick droit", [UI_BIND_L] = "L",
    [UI_BIND_R] = "R", [UI_BIND_ZL] = "ZL", [UI_BIND_ZR] = "ZR", [UI_BIND_PLUS] = "Plus (+)",
    [UI_BIND_MINUS] = "Moins (-)",
    [UI_BIND_LEFT] = "Croix directionnelle gauche", [UI_BIND_UP] = "Croix directionnelle haut",
    [UI_BIND_RIGHT] = "Croix directionnelle droite",
    [UI_BIND_DOWN] = "Croix directionnelle bas",
    [UI_BIND_LSTICK_LEFT] = "Aller à gauche", [UI_BIND_LSTICK_UP] = "Avancer",
    [UI_BIND_LSTICK_RIGHT] = "Aller à droite", [UI_BIND_LSTICK_DOWN] = "Reculer",
    [UI_BIND_RSTICK_LEFT] = "Caméra à gauche", [UI_BIND_RSTICK_UP] = "Caméra vers le haut",
    [UI_BIND_RSTICK_RIGHT] = "Caméra à droite", [UI_BIND_RSTICK_DOWN] = "Caméra vers le bas",
    [UI_BIND_DESC_A] = "Interagir, ramasser, parler.", [UI_BIND_DESC_B] = "Courir, annuler, retour.",
    [UI_BIND_DESC_X] = "Sauter.", [UI_BIND_DESC_Y] = "Attaquer.", [UI_BIND_DESC_LCLICK] = "S'accroupir.",
    [UI_BIND_DESC_RCLICK] = "Vue à la première personne.", [UI_BIND_DESC_L] = "Capacités.",
    [UI_BIND_DESC_R] = "Lancer.", [UI_BIND_DESC_ZL] = "Bouclier, verrouiller.", [UI_BIND_DESC_ZR] = "Arc.",
    [UI_BIND_DESC_PLUS] = "Menu, inventaire.", [UI_BIND_DESC_MINUS] = "Carte.",
    [UI_BIND_DESC_DPAD] = "Sélection rapide.",
    [UI_BIND_DESC_MOVE] = "Déplace comme le stick gauche. Le stick gauche de la manette fonctionne toujours aussi.",
    [UI_BIND_DESC_CAMERA] = "Tourne la caméra comme le stick droit. La souris et le stick droit de la manette "
                            "fonctionnent toujours aussi.",
    [UI_KEY_SPACE] = "Espace", [UI_KEY_TAB] = "Tab", [UI_KEY_LSHIFT] = "Maj gauche", [UI_KEY_LCTRL] = "Ctrl gauche",
    [UI_KEY_UP] = "Flèche haut", [UI_KEY_DOWN] = "Flèche bas", [UI_KEY_LEFT] = "Flèche gauche",
    [UI_KEY_RIGHT] = "Flèche droite",
    [UI_KEY_MOUSE_L] = "Clic gauche", [UI_KEY_MOUSE_R] = "Clic droit", [UI_KEY_MOUSE_M] = "Clic molette",
    [UI_KEY_MOUSE_X1] = "Souris 4", [UI_KEY_MOUSE_X2] = "Souris 5",
    [UI_KEY_ENTER] = "Entrée", [UI_KEY_BACKSPACE] = "Retour arrière", [UI_KEY_RSHIFT] = "Maj droite",
    [UI_KEY_RCTRL] = "Ctrl droite", [UI_KEY_LALT] = "Alt", [UI_KEY_CAPSLOCK] = "Verr Maj", [UI_KEY_INSERT] = "Inser",
    [UI_KEY_DELETE] = "Suppr", [UI_KEY_HOME] = "Début", [UI_KEY_END] = "Fin", [UI_KEY_PAGEUP] = "Page préc.",
    [UI_KEY_PAGEDOWN] = "Page suiv.", [UI_KEY_NUM_FMT] = "Num %s",
    [UI_PAD_SOUTH] = "Bouton du bas", [UI_PAD_EAST] = "Bouton de droite", [UI_PAD_WEST] = "Bouton de gauche",
    [UI_PAD_NORTH] = "Bouton du haut", [UI_PAD_LSTICK] = "Stick gauche", [UI_PAD_RSTICK] = "Stick droit",
    [UI_PAD_L] = "Bouton d'épaule gauche", [UI_PAD_R] = "Bouton d'épaule droit", [UI_PAD_START] = "Start",
    [UI_PAD_BACK] = "Back",
    [UI_PAD_DPAD_LEFT] = "Croix directionnelle gauche", [UI_PAD_DPAD_UP] = "Croix directionnelle haut",
    [UI_PAD_DPAD_RIGHT] = "Croix directionnelle droite",
    [UI_PAD_DPAD_DOWN] = "Croix directionnelle bas", [UI_PAD_ZL] = "Gâchette gauche", [UI_PAD_ZR] = "Gâchette droite",
    [UI_PAD_LPADDLE1] = "Palette arrière gauche", [UI_PAD_RPADDLE1] = "Palette arrière droite",
    [UI_PAD_LPADDLE2] = "Palette arrière gauche 2", [UI_PAD_RPADDLE2] = "Palette arrière droite 2",
    [UI_PAD_CROSS] = "Croix", [UI_PAD_CIRCLE] = "Rond", [UI_PAD_SQUARE] = "Carré", [UI_PAD_TRIANGLE] = "Triangle",

    [UI_MENU_MENU_LANG] = "Langue du menu",
    [UI_MENU_MENU_LANG_DESC] = "Langue de ce menu et des informations à l'écran.",
    [UI_MENU_MENU_LANG_AUTO] = "Automatique (celle de Windows)",

    [UI_MENU_ADV_WARNING] = "Ces paramètres servent aux tests et au dépannage. Ne les modifiez que si vous savez "
                            "pourquoi.",
    [UI_MENU_GROUP_SCHED] = "Ordonnancement", [UI_MENU_GROUP_SHADERS] = "Shaders et pipelines",
    [UI_MENU_GROUP_TEXMEM] = "Textures et mémoire", [UI_MENU_GROUP_FIXES] = "Corrections de rendu",
    [UI_MENU_GROUP_VULKAN] = "Vulkan", [UI_MENU_GROUP_DIAG] = "Diagnostic",
    [UI_MENU_ASYNC_PREEMPT] = "Préemption des cœurs virtuels",
    [UI_MENU_ASYNC_PREEMPT_DESC] = "Permet à un thread du jeu d'en interrompre un autre sur le même cœur virtuel.",
    [UI_MENU_PREEMPT_OFF] = "Désactivée", [UI_MENU_PREEMPT_ON] = "Activée", [UI_MENU_PREEMPT_INHERIT] = "Héritage seul",
    [UI_MENU_REPLAY_ASYNC] = "Préparer les images dans leur propre thread",
    [UI_MENU_REPLAY_ASYNC_DESC] = "Prépare les images pour le GPU dans un thread séparé plutôt que dans le thread du "
                                  "jeu. Ajoute jusqu'à une image de latence.",
    [UI_MENU_TIMER_1MS] = "Minuteur Windows de 1 ms",
    [UI_MENU_TIMER_1MS_DESC] = "Porte la résolution du minuteur système à 1 ms pour un rythme d'images plus stable.",
    [UI_MENU_PIPE_WAIT] = "Traitement des dessins en attente",
    [UI_MENU_PIPE_WAIT_DESC] = "Par défaut conserve l'ordonnancement actuel avec un worker réservé aux dessins en "
                               "attente ; Ancien (dessin) utilise l'ordonnancement précédent.",
    [UI_MENU_PIPE_WAIT_DEFAULT] = "Par défaut", [UI_MENU_PIPE_WAIT_DRAW] = "Ancien (dessin)",
    [UI_MENU_PIPE_SKIP] = "Dessins ignorés pendant la création d'un pipeline",
    [UI_MENU_PIPE_SKIP_DESC] = "Quels dessins sont abandonnés au lieu d'attendre leur pipeline.",
    [UI_MENU_PIPE_SKIP_STRICT] = "Strict", [UI_MENU_PIPE_SKIP_ANY] = "Tous",
    [UI_MENU_PIPE_SKIP_FULLSCREEN] = "Passes plein écran",
    [UI_MENU_LIB_PREBUILD] = "Précompiler les bibliothèques d'étapes",
    [UI_MENU_LIB_PREBUILD_DESC] = "Compile à l'avance et en arrière-plan les bibliothèques d'étapes de shaders.",
    [UI_MENU_LIB_PREBUILD_THREADS] = "Threads de précompilation des bibliothèques",
    [UI_MENU_LIB_PREBUILD_THREADS_DESC] = "Threads utilisés pour précompiler ; « Automatique » choisit un nombre selon "
                                          "votre CPU.",
    [UI_MENU_PIPE_PREBUILD] = "Précompiler les pipelines",
    [UI_MENU_PIPE_PREBUILD_DESC] = "Compile à l'avance les pipelines connus.",
    [UI_MENU_PREWARM_XLATE] = "Préchauffer le traducteur",
    [UI_MENU_PREWARM_XLATE_DESC] = "Threads qui traduisent les shaders connus au démarrage ; « Automatique » utilise "
                                   "la moitié des threads du CPU, 16 au maximum.",
    [UI_MENU_GPL] = "Bibliothèque de pipelines graphiques",
    [UI_MENU_GPL_DESC] = "Utilise l'extension de bibliothèques de pipelines de Vulkan ; désactivez-la si votre pilote "
                         "plante avec elle.",
    [UI_MENU_ASTC] = "Décodage des textures ASTC",
    [UI_MENU_ASTC_DESC] = "Où sont décodées les textures compressées ASTC.",
    [UI_MENU_ASTC_AUTO] = "Automatique", [UI_MENU_ASTC_GPU] = "Shader GPU", [UI_MENU_ASTC_NATIVE] = "Natif",
    [UI_MENU_ASTC_CPU] = "CPU",
    [UI_MENU_MEMORY] = "Mode de mémoire GPU",
    [UI_MENU_MEMORY_DESC] = "Comment la mémoire du jeu est partagée avec le GPU.",
    [UI_MENU_MEMORY_AUTO] = "Automatique", [UI_MENU_MEMORY_IMPORT] = "Importer", [UI_MENU_MEMORY_MIRROR] = "Miroir",
    [UI_MENU_MEMORY_VERIFY] = "Vérifier",
    [UI_MENU_TEX_ALIAS] = "Alias de textures",
    [UI_MENU_TEX_ALIAS_DESC] = "Une nouvelle texture créée sur la mémoire d'une autre encore active commence avec ce "
                               "contenu au lieu d'être vide.",
    [UI_MENU_TEX_VRAM_PRESSURE] = "Limite de mémoire des textures",
    [UI_MENU_TEX_VRAM_PRESSURE_DESC] = "Pourcentage de mémoire vidéo à partir duquel les textures libérées par le jeu "
                                       "sont supprimées (elles reviennent du stockage quand elles sont utilisées). 0 "
                                       "les conserve.",
    [UI_MENU_ASTC_BC] = "Compresser l'ASTC en BC",
    [UI_MENU_ASTC_BC_DESC] = "Avec le décodeur GPU : réencode les textures ASTC décodées en BC1 si elles sont opaques "
                             "et en BC3 sinon, soit entre un quart et un huitième de la mémoire vidéo. Pour les GPU "
                             "de 4 Go ou moins ; les textures paraissent un peu plus pixélisées par blocs.",
    [UI_MENU_LOD_GUARD] = "Protection des LOD",
    [UI_MENU_LOD_GUARD_DESC] = "Évite que des objets clignotent au mauvais endroit ou que l'arrière-plan lointain "
                               "reste plat pendant une image, en attendant que le jeu ait fini de réécrire les "
                               "niveaux de détail avant que le GPU ne les lise.",
    [UI_MENU_FIX_C0] = "Correction du tampon de constantes",
    [UI_MENU_FIX_C0_DESC] = "Remplit la banque de constantes c0 réservée au pilote (tailles de stockage, taille de "
                            "dispatch, taille de point, instance de base) au lieu de lire des zéros.",
    [UI_MENU_FIX_ZERO] = "Mettre à zéro la nouvelle mémoire GPU",
    [UI_MENU_FIX_ZERO_DESC] = "Les nouveaux pools de mémoire GPU commencent à zéro, comme la mémoire de la Switch.",
    [UI_MENU_BIND_SKIP] = "Ignorer les liaisons répétées",
    [UI_MENU_BIND_SKIP_DESC] = "Optimisation : ignore les liaisons qui n'ont pas changé.",
    [UI_MENU_SHADER_MEMO] = "Mémoire des shaders",
    [UI_MENU_SHADER_MEMO_DESC] = "Optimisation : mémorise les recherches de shaders.",
    [UI_MENU_PIPE_MEMO] = "Mémoire des pipelines",
    [UI_MENU_PIPE_MEMO_DESC] = "Optimisation : réutilise le pipeline du dessin précédent quand son état se répète.",
    [UI_MENU_TEX_MEMO] = "Mémoire des liaisons de textures",
    [UI_MENU_TEX_MEMO_DESC] = "Optimisation : mémorise les descripteurs de textures entre les dessins.",
    [UI_MENU_DESC_TEMPLATE] = "Modèles de descripteurs",
    [UI_MENU_DESC_TEMPLATE_DESC] = "Optimisation : met à jour les descripteurs par blocs.",
    [UI_MENU_PUSH_SKIP] = "Ignorer les push constants répétées",
    [UI_MENU_PUSH_SKIP_DESC] = "Optimisation : ignore les push constants qui n'ont pas changé.",
    [UI_MENU_SPLIT_DRAWS] = "Envoi anticipé au GPU",
    [UI_MENU_SPLIT_DRAWS_DESC] = "Envoie le travail du GPU par morceaux tous les N dessins entre les passes pour que "
                                 "le GPU commence plus tôt ; 0 le désactive.",
    [UI_MENU_VK_VALIDATION] = "Couche de validation",
    [UI_MENU_VK_VALIDATION_DESC] = "Vérifie chaque appel Vulkan et ralentit beaucoup le jeu.",
    [UI_MENU_VK_VALIDATION_MISSING] = "La couche de validation n'est pas installée.",
    [UI_MENU_VK_DYN_VERTEX] = "État dynamique des sommets",
    [UI_MENU_VK_DYN_VERTEX_DESC] = "Force l'entrée de sommets dynamique à activée ou désactivée ; la valeur par défaut "
                                   "dépend du GPU.",
    [UI_MENU_VK_DYN_A2C] = "Alpha to coverage dynamique",
    [UI_MENU_VK_DYN_A2C_DESC] = "Force l'alpha to coverage dynamique à activé ou désactivé. Par défaut : désactivé "
                                "avec le pilote AMD pour RDNA 2 et antérieurs, qui dessine alors les personnages en "
                                "noir ; activé dans les autres cas.",
    [UI_MENU_VK_SUBGROUP_PIN] = "Fixer la taille de sous-groupe",
    [UI_MENU_VK_SUBGROUP_PIN_DESC] = "Fixe la taille de sous-groupe des shaders.",
    [UI_MENU_TRACE] = "Journal de performance",
    [UI_MENU_TRACE_DESC] = "Écrit les temps d'image dans un fichier.",
    [UI_MENU_FLIGHT] = "Enregistreur de vol",
    [UI_MENU_FLIGHT_DESC] = "Conserve un court historique et l'écrit quand une image se fige.",
    [UI_MENU_FLIGHT_SPIKE_MS] = "Seuil de blocage (ms)",
    [UI_MENU_FLIGHT_SPIKE_MS_DESC] = "Temps d'image considéré comme un blocage.",
    [UI_MENU_INPUT_RECORD] = "Enregistrer les entrées",
    [UI_MENU_INPUT_RECORD_DESC] = "Écrit vos appuis dans un fichier pour signaler des bugs.",
    [UI_MENU_OPEN_LOG] = "Ouvrir le dossier des journaux",
    [UI_MENU_OPEN_LOG_DESC] = "Affiche le dossier contenant les journaux.",
    [UI_MENU_COPY_INFO] = "Copier les informations système",
    [UI_MENU_COPY_INFO_DESC] = "Copie dans le presse-papiers le GPU, le pilote, le CPU, la RAM et les paramètres "
                               "modifiés.",
    [UI_MENU_COPY_INFO_DONE] = "Copié", [UI_MENU_ACTION_FAILED] = "échec",
    [UI_MENU_RESET] = "Réinitialiser tous les paramètres", [UI_MENU_RESET_DESC] = "S'applique à tous les onglets.",
    [UI_MENU_RESET_CONFIRM] = "Réinitialiser tous les paramètres à leurs valeurs par défaut ?",
    [UI_MENU_RESET_YES] = "Réinitialiser",
    [UI_MENU_RESET_NO] = "Annuler",

    [UI_MENU_OV_FPS] = "%.0f FPS", [UI_MENU_OV_FRAME_MS] = "%.1f ms", [UI_MENU_OV_GAME_PCT] = "jeu %.0f%%",
    [UI_MENU_OV_MAX_MS] = "max. %.1f ms",
    [UI_MENU_OV_GPU] = "GPU", [UI_MENU_OV_CPU] = "CPU", [UI_MENU_OV_RAM] = "RAM", [UI_MENU_OV_VRAM] = "VRAM",
    [UI_MENU_OV_TEMP] = "Température", [UI_MENU_OV_POWER] = "Consommation", [UI_MENU_OV_CLOCK] = "Fréquence",
    [UI_MENU_OV_NONE] = "-",
    [UI_MENU_OV_REPLAY] = "Préparation des images", [UI_MENU_OV_GPU_TIME] = "GPU occupé par image",
    [UI_MENU_OV_PIPE_WAIT] = "Attentes de pipelines",
    [UI_MENU_OV_SHADER_WAIT] = "Attentes de shaders", [UI_MENU_OV_TEX_UPLOADS] = "Envois de textures",
    [UI_MENU_OV_FMT_PCT] = "%.0f%%", [UI_MENU_OV_FMT_TEMP] = "%.0f °C", [UI_MENU_OV_FMT_POWER] = "%.0f W",
    [UI_MENU_OV_FMT_MHZ] = "%.0f MHz", [UI_MENU_OV_FMT_GB] = "%.1f Go", [UI_MENU_OV_FMT_GB_OF] = "/ %.1f Go",
    [UI_MENU_OV_GAME_GB] = "jeu %.1f Go", [UI_MENU_OV_FMT_MS] = "%.2f ms", [UI_MENU_OV_PER_FRAME] = "%.1f par image",
    [UI_MENU_OV_WINDOW] = "Fenêtre", [UI_MENU_OV_OUTPUT] = "Image du jeu", [UI_MENU_OV_SCENE] = "Scène 3D",
    [UI_MENU_OV_SCALING] = "Mise à l'échelle", [UI_MENU_OV_LIMIT] = "Limite de FPS",
    [UI_MENU_OV_PRESENT] = "Présentation",
    [UI_MENU_OV_TEX] = "Compression des textures", [UI_MENU_OV_OS] = "Système",
    [UI_MENU_OV_FMT_SIZE] = "%ux%u", [UI_MENU_OV_FMT_SCENE] = "%ux%u, %.0f%%",
    [UI_MENU_OV_FMT_FSR] = "AMD FSR 1, netteté %d%%", [UI_MENU_OV_SCALE_NONE] = "aucune (1:1)",
    [UI_MENU_OV_SCALE_BILINEAR] = "bilinéaire",
    [UI_MENU_OV_FMT_AREA] = "moyenne de zone, netteté %d%%",
    [UI_MENU_OV_FMT_PRESHARP] = "RCAS avant le HUD, netteté %d%%",
    [UI_MENU_TAB_CHEATS] = "Triche",
    [UI_MENU_CHEATS_NONE] = "Aucun code de triche pour cette version du jeu. Les codes de triche d'un mod sont un "
                            "fichier de codes Atmosphere dans son dossier cheats, portant le nom du build du jeu : "
                            "mods\\<mod>\\cheats\\%s. Redémarrez le jeu pour les lire. Pour les codes qui modifient "
                            "le code du jeu, le jeu est reconstruit au démarrage (quelques minutes).",
    [UI_MENU_CHEATS_MOD] = "%s : %d codes de triche",
    [UI_MENU_CHEAT_CODE_DESC] = "Modifie le code du jeu. S'active immédiatement.",
    [UI_MENU_CHEAT_KEY_DESC] = "Modifie le code du jeu tant que vous maintenez %s. S'active immédiatement.",
    [UI_MENU_CHEAT_DATA_DESC] = "Écrit dans la mémoire du jeu à chaque image tant qu'il est activé.",
    [UI_MENU_CHEAT_MASTER] = "toujours activé",
    [UI_MENU_CHEAT_MASTER_DESC] = "Le code maître du fichier : il est toujours activé.",
    [UI_MENU_CHEAT_RESTORE] = "inutile",
    [UI_MENU_CHEAT_RESTORE_DESC] = "Ne fait que réécrire le code d'origine du jeu. Désactiver un code de triche le "
                                   "fait déjà.",
    [UI_MENU_CHEAT_REBUILD] = "après la reconstruction",
    [UI_MENU_CHEAT_REBUILD_DESC] = "Ce code de triche modifie le code du jeu et il est nouveau ou a été modifié "
                                   "depuis la construction du jeu. Le jeu l'intègre au prochain démarrage (quelques "
                                   "minutes), ou utilisez Reconstruire le jeu maintenant.",
    [UI_MENU_CHEAT_UNSUPPORTED] = "non pris en charge",
    [UI_MENU_CHEAT_UNSUPPORTED_DESC] = "Ce code de triche ne peut pas être utilisé avec cette version du jeu :",
    [UI_MENU_CHEATS_REBUILD] = "Reconstruire le jeu maintenant",
    [UI_MENU_CHEATS_REBUILD_DESC] = "Certains codes de triche modifient le code du jeu et ne sont pas intégrés : ils "
                                    "sont nouveaux ou ont été modifiés, ou leur dernière reconstruction a échoué ou a "
                                    "été annulée. Ferme le jeu ; l'installation les intègre (quelques minutes) et "
                                    "rouvre le jeu. La progression depuis votre dernière sauvegarde est perdue.",
    [UI_MENU_MODS_EXEFS_UNSUPPORTED] = "Ce mod patche le code du jeu (exefs) d'une manière que le portage ne peut pas "
                                       "appliquer, le mod entier est donc désactivé. %s",
    [UI_MENU_MODS_EXEFS_OTHER] = "Ses patchs de code (exefs) sont destinés à une autre version du jeu.",
    [UI_MENU_MODS_EXEFS_ON] = "Patchs de code utilisés : %d fichiers.",
    [UI_MENU_MODS_REPLACES_BUILTIN] = "Patchs de code utilisés : %d fichiers. Ils remplacent le patch %s propre au "
                                      "portage, qui reste désactivé tant que ce mod est activé.",
};
