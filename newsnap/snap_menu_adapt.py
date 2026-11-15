"""MENU-02: the in-game Screen page shows Snap's own options, greyed out with the reason where they cannot apply.

The donor's "Game resolution" (AC_OUTPUT_RES) has no effect in Snap, which always draws at 1920x1080: it is replaced by
"Game internal resolution" (AC_RENDER_SCALE, the launcher's choices). After the upscaler rows: frame generation (needs
FSR 3.1/4 running), HD photo thumbnails, shadow resolution with Auto, the HD texture pack (needs one) and the aspect
ratio with ultrawide. Ids past UI_MENU_LAST_ID: English text only, the menu's other languages fall back to it.
"""

IDS = ('UI_SNAP_RES', 'UI_SNAP_RES_DESC', 'UI_SNAP_RES_UPSCALER', 'UI_SNAP_FG', 'UI_SNAP_FG_DESC', 'UI_SNAP_FG_NEEDS',
       'UI_SNAP_HDPH', 'UI_SNAP_HDPH_DESC', 'UI_SNAP_SHADOW', 'UI_SNAP_SHADOW_DESC', 'UI_SNAP_TEXPACK',
       'UI_SNAP_TEXPACK_DESC', 'UI_SNAP_TEXPACK_NONE', 'UI_SNAP_ASPECT', 'UI_SNAP_ASPECT_DESC')

TEXTS = {
    'UI_SNAP_RES': 'Game internal resolution',
    'UI_SNAP_RES_DESC': 'The resolution the 3D scene is drawn at, relative to the game\'s 1920 x 1080. Below 100 % is '
                        'lighter; above 100 % (supersampling) is sharper and costs GPU time. By display matches the '
                        'screen or window height. Above 100 % applies while no upscaler runs. Takes effect after a restart.',
    'UI_SNAP_RES_UPSCALER': 'above 100 %: set Upscaler to Original',
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
    static const char *const vals[] = {"game", "50", "60", "70", "80", "90", "100", "125", "133", "150", "175", "200",
                                       "250", "300", "display"};
    static const char *const names[] = {"Game (100 %)", "50 %", "60 %", "70 %", "80 %", "90 %", "100 %", "125 %",
                                        "133 %", "150 %", "175 %", "200 %", "250 %", "300 %", "By display"};
    enum { N = sizeof vals / sizeof *vals };
    const char *v = cfg_value("AC_RENDER_SCALE");
    int above = !strcmp(v, "display") || atoi(v) > 100;
    opt_choice_list("AC_RENDER_SCALE", UI_SNAP_RES, vals, names, N, UI_SNAP_RES_DESC, -1,
                    above && snap_upscaler_on() ? menu_text(UI_SNAP_RES_UPSCALER) : nullptr);
}

static void snap_rows_snap(void) {
    {
        static const char *const vals[] = {"off", "fsr"};
        static const char *const names[] = {"Off", "AMD FSR (1 generated frame)"};
        const char *runs = vk_dlaa_upscaler_name();
        const char *up = cfg_upscaling();
        bool fsr = (runs && strstr(runs, "FSR")) || !strcmp(up, "fsr3") || !strcmp(up, "fsr4");
        if (!fsr) opt_disable_next(UI_SNAP_FG_NEEDS);
        opt_choice_list("AC_FRAME_GEN", UI_SNAP_FG, vals, names, 2, UI_SNAP_FG_DESC);
    }
    opt_toggle("AC_HD_PHOTOS", UI_SNAP_HDPH, UI_SNAP_HDPH_DESC);
    {
        static const char *const vals[] = {"1", "2", "4", "auto"};
        static const char *const names[] = {"1x (original)", "2x", "4x", "Auto (3D resolution)"};
        opt_choice_list("AC_SHADOW_SCALE", UI_SNAP_SHADOW, vals, names, 4, UI_SNAP_SHADOW_DESC);
    }
    {
        static char note[64];
        int n = snap_texpack_files();
        if (n <= 0) opt_disable_next(UI_SNAP_TEXPACK_NONE);
        else snprintf(note, sizeof note, "%d textures", n);
        opt_toggle("AC_TEX_PACK", UI_SNAP_TEXPACK, UI_SNAP_TEXPACK_DESC);
        (void)note;
    }
    {
        static const char *const vals[] = {"fit", "stretch", "ultrawide"};
        static const char *const names[] = {"Keep 16:9", "Stretch", "Ultrawide (wider view)"};
        opt_choice_list("AC_ASPECT", UI_SNAP_ASPECT, vals, names, 3, UI_SNAP_ASPECT_DESC);
    }
}

'''


def edits():
    ids = ''.join(f'    {name},\n' for name in IDS)
    texts = ''.join('    [{}] = "{}",\n'.format(k, v.replace('"', '\\"')) for k, v in TEXTS.items())
    return {
        'runtime/cfg.c': [
            ('{"WINDOW_SIZE", "1920x1080", NULL, LIVE}', '{"WINDOW_SIZE", "auto", NULL, LIVE}'),
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
            ('    row_output_res();\n    rows_upscaling();', '    snap_row_internal_res();\n    rows_upscaling();\n    snap_rows_snap();'),
        ],
    }
