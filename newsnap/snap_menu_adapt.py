"""MENU-02: the in-game Screen page shows Snap's own options, greyed out with the reason where they cannot apply.

The donor's "Game resolution" (AC_OUTPUT_RES) has no effect in Snap, which always draws at 1920x1080: it is replaced by
"Game internal resolution" (AC_RENDER_SCALE, the launcher's choices). After the upscaler rows: frame generation (needs
FSR 3.1/4 running), HD photo thumbnails, shadow resolution with Auto, the HD texture pack (needs one) and the aspect
ratio with ultrawide. Ids past UI_MENU_LAST_ID: English text only, the menu's other languages fall back to it.
"""

IDS = ('UI_SNAP_RES', 'UI_SNAP_RES_DESC', 'UI_SNAP_RES_UPSCALER', 'UI_SNAP_FG', 'UI_SNAP_FG_DESC', 'UI_SNAP_FG_NEEDS',
       'UI_SNAP_HDPH', 'UI_SNAP_HDPH_DESC', 'UI_SNAP_SHADOW', 'UI_SNAP_SHADOW_DESC', 'UI_SNAP_TEXPACK',
       'UI_SNAP_TEXPACK_DESC', 'UI_SNAP_TEXPACK_NONE', 'UI_SNAP_ASPECT', 'UI_SNAP_ASPECT_DESC', 'UI_SNAP_TAB',
       'UI_SNAP_ENH', 'UI_SNAP_HDSH', 'UI_SNAP_HDSH_DESC', 'UI_SNAP_TAB_SYS', 'UI_SNAP_SYS_CONT', 'UI_SNAP_SYS_CONT_DESC',
       'UI_SNAP_SYS_RESTART', 'UI_SNAP_SYS_RESTART_DESC', 'UI_SNAP_SYS_QUIT', 'UI_SNAP_SYS_QUIT_DESC')

TEXTS = {
    'UI_SNAP_RES': 'Game internal resolution',
    'UI_SNAP_RES_DESC': 'The resolution the 3D scene is drawn at. 100 % is the game\'s own 1920 x 1080: go down for a '
                        'lighter picture, up (supersampling) for a sharper one that costs GPU time. By display matches '
                        'the screen or window height. Above 100 % needs no upscaler: Automatic then uses Original by '
                        'itself, a chosen upscaler has to be set to Original. Takes effect after a restart.',
    'UI_SNAP_RES_UPSCALER': 'above 100 %: set Upscaler to Original or Automatic',
    'UI_SNAP_FG': 'Frame generation',
    'UI_SNAP_FG_DESC': 'AMD FSR frame generation: one generated frame between two real ones. The interface is kept out of '
                       'the interpolation. It pauses itself while the game runs faster than about half the monitor\'s '
                       'refresh. The performance overlay shows real fps and the generated ones. Takes effect after a restart.',
    'UI_SNAP_FG_NEEDS': 'needs AMD FSR 3.1 or FSR 4 as the upscaler',
    'UI_SNAP_HDPH': 'HD photo thumbnails',
    'UI_SNAP_HDPH_DESC': 'The preview after a shot and the photos on the folder and selection screens use the 1080 x 720 '
                         'photo instead of the game\'s 360 x 240 thumbnail. Saved photos and scores do not change.',
    'UI_SNAP_SHADOW': 'Shadow resolution',
    'UI_SNAP_SHADOW_DESC': 'Enlarges every shadow map of the game. Auto follows the 3D resolution: 2x at 1080p, 3x at '
                           '125-150 %, 4x from 200 %. Shadows painted into the scenery textures do not change. '
                           'Takes effect after a restart.',
    'UI_SNAP_TEXPACK': 'HD texture pack',
    'UI_SNAP_TEXPACK_DESC': 'Uses the HD textures in the texpack folder next to the game, made on this PC from your own '
                            'game. Takes effect after a restart.',
    'UI_SNAP_TEXPACK_NONE': 'no pack in the texpack folder',
    'UI_SNAP_HDSH': 'HD shadows mode (AI, experimental)',
    'UI_SNAP_HDSH_DESC': 'The shadows of plants, rocks and scenery are painted into the light maps of each level. On: each '
                         'light map is saved the first time it loads, and Generate HD shadows in the launcher enlarges '
                         'them on this PC; the HD ones are used the next time the level loads. Takes effect after a restart.',
    'UI_SNAP_TAB_SYS': 'System',
    'UI_SNAP_SYS_CONT': 'Back to the game',
    'UI_SNAP_SYS_CONT_DESC': 'Closes this menu and goes on playing.',
    'UI_SNAP_SYS_RESTART': 'Restart the game',
    'UI_SNAP_SYS_RESTART_DESC': 'Closes the game and starts it again, for settings that apply after a restart. Progress since your last save is lost.',
    'UI_SNAP_SYS_QUIT': 'Quit to desktop',
    'UI_SNAP_SYS_QUIT_DESC': 'Closes the game. Progress since your last save is lost; the game saves on its own after each expedition.',
    'UI_SNAP_TAB': 'Enhancements',
    'UI_SNAP_ENH': 'NewSnap enhancements (they do not change the game\'s logic)',
    'UI_SNAP_ASPECT': 'Aspect ratio',
    'UI_SNAP_ASPECT_DESC': 'Keep 16:9 adds bars on wider screens; Stretch fills the window; Ultrawide widens the 3D view to '
                           'the window with the game\'s proportions, keeps the interface in the middle and takes photos '
                           'with the usual 16:9 view (experimental).',
}

FUNCS = r'''// MENU-02 (newsnap/snap_menu_adapt.py): Snap's own rows on the Screen page.
extern "C" int snap_texpack_files(void);
extern "C" float snap_scene_scale(void);

static bool snap_upscaler_on(void) { return strcmp(cfg_upscaling(), "off") != 0; }

static void snap_row_internal_res(void) {
    // MENU-03: one scale with the game's own 100 % in the middle, lighter below it and sharper above it; By display
    // last. 100 % stores "game" (the default); a stored "100" is the same picture and shows as it.
    static const char *const vals[] = {"50", "60", "70", "80", "90", "game", "125", "133", "150", "175", "200",
                                       "250", "300", "display"};
    static const char *const names[] = {"50 % (lightest)", "60 %", "70 %", "80 %", "90 %", "100 % (the game's)", "125 %",
                                        "133 %", "150 %", "175 %", "200 %", "250 %", "300 % (sharpest)", "By display"};
    enum { N = sizeof vals / sizeof *vals, NATIVE = 5 };
    const char *v = cfg_value("AC_RENDER_SCALE");
    int cur = NATIVE;
    for (int i = 0; i < N; i++) if (!strcmp(v, vals[i])) cur = i;
    int above = !strcmp(v, "display") || atoi(v) > 100;
    opt_choice_list("AC_RENDER_SCALE", UI_SNAP_RES, vals, names, N, UI_SNAP_RES_DESC, cur,
                    above && snap_upscaler_on() ? menu_text(UI_SNAP_RES_UPSCALER) : nullptr);
}

static void snap_rows_enhancements(void) {
    opt_toggle("AC_HD_PHOTOS", UI_SNAP_HDPH, UI_SNAP_HDPH_DESC);
    opt_toggle("AC_HD_SHADOWS", UI_SNAP_HDSH, UI_SNAP_HDSH_DESC);
    {
        static char note[64];
        int n = snap_texpack_files();
        if (n <= 0) opt_disable_next(UI_SNAP_TEXPACK_NONE);
        else snprintf(note, sizeof note, "%d textures", n);
        opt_toggle("AC_TEX_PACK", UI_SNAP_TEXPACK, UI_SNAP_TEXPACK_DESC);
        (void)note;
    }
    {
        static const char *const vals[] = {"off", "fsr"};
        static const char *const names[] = {"Off", "AMD FSR (1 generated frame)"};
        const char *runs = vk_dlaa_upscaler_name();
        const char *up = cfg_upscaling();
        bool fsr = (runs && strstr(runs, "FSR")) || !strcmp(up, "fsr3") || !strcmp(up, "fsr4");
        if (!fsr) opt_disable_next(UI_SNAP_FG_NEEDS);
        opt_choice_list("AC_FRAME_GEN", UI_SNAP_FG, vals, names, 2, UI_SNAP_FG_DESC);
    }
}

static void snap_row_aspect(void) {
    static const char *const vals[] = {"fit", "stretch", "ultrawide"};
    static const char *const names[] = {"Keep 16:9", "Stretch", "Ultrawide (wider view)"};
    opt_choice_list("AC_ASPECT", UI_SNAP_ASPECT, vals, names, 3, UI_SNAP_ASPECT_DESC);
}

// The Enhancements tab, in the place of the donor's Mods tab: NewSnap's own improvements, each one switchable.
static void snap_tab_enhancements(float scale) {
    opt_begin("##snapenh", scale);
    opt_group(UI_SNAP_ENH);
    snap_rows_enhancements();
    opt_end();
}

'''

SYSTEM_TAB = '''// MENU-04: the System tab, last: back to the game, restart the game, quit to the desktop.
static void snap_tab_system(float scale) {
    opt_begin("##snapsys", scale);
    bool back = opt_button("##snapcont", UI_SNAP_SYS_CONT, UI_SNAP_SYS_CONT_DESC);
    bool restart = opt_button("##restart", UI_SNAP_SYS_RESTART, UI_SNAP_SYS_RESTART_DESC);
    bool quit = opt_button("##snapquit", UI_SNAP_SYS_QUIT, UI_SNAP_SYS_QUIT_DESC);
    opt_end();
    if (back) set_open(0);
    if (quit) gfx_window_request_close();
    if (restart) ImGui::OpenPopup("##restart_confirm");
    restart_confirm();
}

'''


def edits():
    ids = ''.join(f'    {name},\n' for name in IDS)
    texts = ''.join('    [{}] = "{}",\n'.format(k, v.replace('"', '\\"')) for k, v in TEXTS.items())
    return {
        'runtime/cfg.c': [
            ('{"WINDOW_SIZE", "1920x1080", NULL, LIVE}', '{"WINDOW_SIZE", "auto", NULL, LIVE}'),
            # MENU-03: supersampling only runs without an upscaler, so Automatic steps aside by itself when the
            # internal resolution asks for more than 100 %. A chosen upscaler is never overridden.
            ('const char *cfg_upscaling(void) {\n    const char *l = legacy_upscaler();\n'
             '    return l ? l : cfg_value(PREFIX "UPSCALING");\n}',
             'int snap_auto_upscaler_off(void);   // snap_desktop.c\n'
             'const char *cfg_upscaling(void) {\n    const char *l = legacy_upscaler();\n'
             '    const char *up = l ? l : cfg_value(PREFIX "UPSCALING");\n'
             '    return !l && !strcmp(up, "auto") && snap_auto_upscaler_off() ? "off" : up;\n}'),
        ],
        'runtime/gfx_present.c': [
            ('void gfx_cfg_window_size(int *w, int *h) {\n    int x = 0, y = 0;\n',
             'int snap_desktop_size(int *w, int *h);\n'
             'void gfx_cfg_window_size(int *w, int *h) {\n    int x = 0, y = 0;\n'
             '    if (!strcmp(cfg_value("AC_WINDOW_SIZE"), "auto") && snap_desktop_size(&x, &y)) {   // MENU-02: the desktop\'s size\n'
             '        *w = x, *h = y;\n        return;\n    }\n'),
        ],
        'runtime/ui_text.h': [
            ('    UI_MENU_LAST_ID = UI_MENU_CHEAT_UNSUPPORTED_DESC,\n    UI_TEXT_COUNT',
             '    UI_MENU_LAST_ID = UI_MENU_CHEAT_UNSUPPORTED_DESC,\n' + ids + '    UI_TEXT_COUNT'),
        ],
        'runtime/ui_text.c': [
            ('    [UI_MENU_AA_BY_UPSCALER] = "the upscaler smooths the edges",\n',
             '    [UI_MENU_AA_BY_UPSCALER] = "the upscaler smooths the edges",\n' + texts),
            # MENU-04: the whole menu in Spanish (overlays/ui_text_es.inc) in place of the keyboard-only row
            ('SWKBD_ONLY(text_es, "Introducir texto", "Introduce un nombre", "Caballo", "Aceptar", "Cancelar",\n'
             '           "Mando: A = Aceptar, B = Cancelar");\n',
             '#include "ui_text_es.inc"\n'),
        ],
        'runtime/ui/menu.cpp': [
            ('    opt_choice_list("AC_WINDOW_SIZE", UI_MENU_WINDOW_SIZE, pv, pn, n, UI_MENU_WINDOW_SIZE_DESC);',
             '    const char *av[MAX_SIZES + 1], *an[MAX_SIZES + 1];   // MENU-02: Automatic (the desktop\'s size) first\n'
             '    av[0] = "auto", an[0] = "Automatic (desktop)";\n'
             '    for (int i = 0; i < n; i++) av[i + 1] = pv[i], an[i + 1] = pn[i];\n'
             '    opt_choice_list("AC_WINDOW_SIZE", UI_MENU_WINDOW_SIZE, av, an, n + 1, UI_MENU_WINDOW_SIZE_DESC);'),
            ('    unsigned rw = scene[0], rh = scene[1];\n    char v[6][64];',
             '    float snap_k = snap_scene_scale();   // MENU-02: the 3D size after the internal-resolution scale\n'
             '    unsigned rw = (unsigned)(scene[0] * snap_k + 0.5f), rh = (unsigned)(scene[1] * snap_k + 0.5f);\n    char v[6][64];'),
            ('    if (hz > 0) snprintf(v[4], sizeof v[4], menu_text(UI_MENU_OV_FPS), hz);\n',
             '    if (hz > 0) snprintf(v[4], sizeof v[4], menu_text(UI_MENU_OV_FPS), hz);\n'
             '    if (strcmp(cfg_value("AC_FRAME_GEN"), "off")) {   // MENU-02: frame generation on\n'
             '        size_t used = strlen(v[4]);\n'
             '        snprintf(v[4] + used, sizeof v[4] - used, " + FG");\n'
             '    }\n'),
            ('static void rows_upscaling(void) {', FUNCS + 'static void rows_upscaling(void) {'),
            ('    row_output_res();\n    rows_upscaling();', '    snap_row_internal_res();\n    rows_upscaling();\n    snap_row_aspect();'),
            ('UI_MENU_TAB_CONTROLS, UI_MENU_TAB_MENU,   UI_MENU_TAB_MODS};', 'UI_MENU_TAB_CONTROLS, UI_MENU_TAB_MENU,   UI_SNAP_TAB};'),
            ('            case TAB_MODS: tab_mods(scale); break;', '            case TAB_MODS: snap_tab_enhancements(scale); break;\n'
             '            case TAB_SYSTEM: snap_tab_system(scale); break;'),
            # MENU-04: a last tab, System: back to the game, restart, quit to the desktop
            ('enum { TAB_SCREEN, TAB_GAME, TAB_SOUND, TAB_CONTROLS, TAB_MENU, TAB_MODS, TAB_COUNT };',
             'enum { TAB_SCREEN, TAB_GAME, TAB_SOUND, TAB_CONTROLS, TAB_MENU, TAB_MODS, TAB_SYSTEM, TAB_COUNT };'),
            ('static const UiTextId kTabNames[TAB_COUNT] = {', SYSTEM_TAB + 'static const UiTextId kTabNames[TAB_COUNT] = {'),
            ('UI_MENU_TAB_MENU,   UI_SNAP_TAB};', 'UI_MENU_TAB_MENU,   UI_SNAP_TAB, UI_SNAP_TAB_SYS};'),
            # the menu in every language of the game that has its text (ui_text_*.inc)
            ('    static const UiTextId langs[] = {UI_MENU_MENU_LANG_AUTO, UI_MENU_LANGNAME_EN, UI_MENU_LANGNAME_RU,\n'
             '                                     UI_MENU_LANGNAME_PT_BR, UI_MENU_LANGNAME_ZH_HANS};',
             '    static const UiTextId langs[] = {UI_MENU_MENU_LANG_AUTO, UI_MENU_LANGNAME_EN, UI_MENU_LANGNAME_ES,\n'
             '                                     UI_MENU_LANGNAME_RU, UI_MENU_LANGNAME_PT_BR, UI_MENU_LANGNAME_ZH_HANS};'),
        ],
    }
