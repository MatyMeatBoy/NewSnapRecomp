"""In-game Snap temporal choices; names and presets match the actual providers."""


def edits():
    return {'runtime/ui/menu.cpp': [
        ('''    static const char *const vals[] = {"off", "auto", "dlss", "xess", "fsr3"};
    const char *names[] = {menu_text(UI_MENU_UPSCALING_OFF), menu_text(UI_MENU_UPSCALING_AUTO), "NVIDIA DLSS",
                           "Intel XeSS", "AMD FSR 3"};''',
         '''    static const char *const vals[] = {"off", "auto", "dlss", "fsr3", "fsr4"};
    const char *names[] = {"Original", menu_text(UI_MENU_UPSCALING_AUTO), "NVIDIA DLSS",
                           "AMD FSR 3.1", "AMD FSR 4"};'''),
        ('''    static const char *const vals[] = {"off", "auto", "fsr3"};
    const char *names[] = {menu_text(UI_MENU_UPSCALING_OFF), menu_text(UI_MENU_UPSCALING_AUTO), "AMD FSR 3"};''',
         '''    static const char *const vals[] = {"off", "auto", "fsr3", "fsr4"};
    const char *names[] = {"Original", menu_text(UI_MENU_UPSCALING_AUTO), "AMD FSR 3.1", "AMD FSR 4"};'''),
        ('''        static const char *const qv[] = {"native", "quality", "balanced", "performance", "ultra_performance"};
        const char *qn[] = {menu_text(UI_MENU_UPSCALING_NATIVE), menu_text(UI_MENU_DLSS_QUALITY),
                            menu_text(UI_MENU_DLSS_BALANCED), menu_text(UI_MENU_DLSS_PERFORMANCE),
                            menu_text(UI_MENU_UPSCALING_ULTRA)};''',
         '''        static const char *const qv[] = {"native", "quality", "balanced", "performance"};
        const char *qn[] = {"Native AA / DLAA (100%)", menu_text(UI_MENU_DLSS_QUALITY),
                            menu_text(UI_MENU_DLSS_BALANCED), menu_text(UI_MENU_DLSS_PERFORMANCE)};'''),
        ('        for (int i = 0; i < 5; i++)\n            if (!strcmp(q, qv[i])) qcur = i;',
         '        for (int i = 0; i < 4; i++)\n            if (!strcmp(q, qv[i])) qcur = i;'),
        ('UI_MENU_UPSCALING_QUALITY, qv, qn, 5,', 'UI_MENU_UPSCALING_QUALITY, qv, qn, 4,'),
        ('''    static const UiTextId up[] = {UI_MENU_UPSCALER_FSR, UI_MENU_UPSCALER_BILINEAR};
    opt_choice("AC_UPSCALER", UI_MENU_UPSCALER, up, 2, UI_MENU_UPSCALER_DESC);
    opt_slider("AC_SHARPNESS", UI_MENU_SHARPNESS, 0, 100, UI_MENU_SHARPNESS_DESC, 5, "%.0f %%");''',
         '    // Snap presents its original SDR output without an additional spatial FSR/sharpening stage.'),
        ('''static void row_shadow_scale(void) {
    static const char *const vals[] = {"1", "2", "3", "4"};
    static const char *const names[] = {"2048 (1x)", "4096 (2x)", "6144 (3x)", "8192 (4x)"};
    opt_choice_list("AC_SHADOW_SCALE", UI_MENU_SHADOW_SCALE, vals, names, 4, UI_MENU_SHADOW_SCALE_DESC);
}

''', ''),
        ('''static void rows_color(void) {
    static const struct { const char *name, *b, *c, *s, *g; } presets[] = {
        {"default", "0", "100", "100", "1"}, {"vivid", "0", "115", "135", "0.95"}, {"clarity", "2", "110", "115", "1"}};
    static const UiTextId names[] = {UI_MENU_COLOR_DEFAULT, UI_MENU_COLOR_VIVID, UI_MENU_COLOR_CLARITY,
                                     UI_MENU_COLOR_CUSTOM};
    opt_group(UI_MENU_COLOR);
    if (opt_choice("AC_COLOR_PRESET", UI_MENU_COLOR_PRESET, names, 4, UI_MENU_COLOR_PRESET_DESC)) {
        const char *p = cfg_value("AC_COLOR_PRESET");
        for (const auto &e : presets)
            if (!strcmp(p, e.name)) {
                cfg_set("AC_COLOR_BRIGHTNESS", e.b), cfg_set("AC_COLOR_CONTRAST", e.c);
                cfg_set("AC_COLOR_SATURATION", e.s), cfg_set("AC_COLOR_GAMMA", e.g);
                cfg_save();
            }
    }
    bool moved = opt_slider("AC_COLOR_BRIGHTNESS", UI_MENU_COLOR_BRIGHTNESS, -30, 30, UI_MENU_COLOR_BRIGHTNESS_DESC, 1,
                            "%+.0f %%");
    moved |= opt_slider("AC_COLOR_CONTRAST", UI_MENU_COLOR_CONTRAST, 70, 150, UI_MENU_COLOR_CONTRAST_DESC, 5, "%.0f %%");
    moved |= opt_slider("AC_COLOR_SATURATION", UI_MENU_COLOR_SATURATION, 50, 200, UI_MENU_COLOR_SATURATION_DESC, 5,
                        "%.0f %%");
    moved |= opt_slider("AC_COLOR_GAMMA", UI_MENU_COLOR_GAMMA, 0.8f, 1.2f, UI_MENU_COLOR_GAMMA_DESC, 0.02f, "%.2f");
    if (moved && strcmp(cfg_value("AC_COLOR_PRESET"), "custom")) {
        cfg_set("AC_COLOR_PRESET", "custom");
        cfg_save();
    }
}

''', ''),
        ('''    row_shadow_scale();
    static const UiTextId ao[] = {UI_MENU_AO_OFF, UI_MENU_AO_LOW, UI_MENU_AO_HIGH};
    opt_choice("AC_AO", UI_MENU_AO, ao, 3, UI_MENU_AO_DESC);
    rows_color();
    opt_group(UI_MENU_HDR_GROUP);
    opt_toggle("AC_HDR", UI_MENU_HDR, UI_MENU_HDR_DESC);
    opt_slider("AC_HDR_PEAK_NITS", UI_MENU_HDR_PEAK, 400, 10000, UI_MENU_HDR_PEAK_DESC, 50, "%.0f");
    // 1-nit steps; held, a row moves ten at a time over this range (option_rows.cpp opt_slider)
    opt_slider("AC_HDR_GAME_NITS", UI_MENU_HDR_GAME, 80, 500, UI_MENU_HDR_GAME_DESC, 1, "%.0f");
    opt_slider("AC_HDR_UI_NITS", UI_MENU_HDR_UI, 80, 500, UI_MENU_HDR_UI_DESC, 1, "%.0f");
    opt_slider("AC_HDR_HUE", UI_MENU_HDR_HUE, 0, 100, UI_MENU_HDR_HUE_DESC, 5, "%.0f %%");''',
         '    // Original Snap color, shadows and SDR output are preserved by the neutral native policy.'),
    ]}
