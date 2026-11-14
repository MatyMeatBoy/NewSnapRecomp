"""Guarded product-facing names; donor attribution and AC_* compatibility remain intact.

Apply through adapt.replace_once: each literal anchor is expected exactly once.
Legacy logs are never migrated; only the new product log family is rotated.
"""


def edits():
    changes = _visible_edits()
    changes['runtime/ui_text.c'].extend([
        ('    [UI_MENU_VERSION] = "Astral Chain Recomp %s, game %s",',
         '    [UI_MENU_VERSION] = "NewSnapRecomp %s, Snap %s",'),
        ('    [UI_MENU_VERSION] = "Astral Chain Recomp %s, игра %s",',
         '    [UI_MENU_VERSION] = "NewSnapRecomp %s, Snap %s",'),
        ('    [UI_MENU_VERSION] = "Astral Chain Recomp %s, jogo %s",',
         '    [UI_MENU_VERSION] = "NewSnapRecomp %s, Snap %s",'),
        ('    [UI_MENU_VERSION] = "Astral Chain Recomp %s，游戏 %s",',
         '    [UI_MENU_VERSION] = "NewSnapRecomp %s, Snap %s",'),
    ])
    changes['runtime/cfg.c'].extend([
        ('static int save_ok = 1;                         // the last cfg_save_to wrote (or had nothing to write)',
         'static int save_ok = 1;                         // the last cfg_save_to wrote (or had nothing to write)\n'
         '// Legacy settings are a read-only source until the first changed-key save.\n'
         'static char snap_legacy_ini[1024], snap_primary_ini[1024];'),
        ('    if (!cut || cut + 10 >= path + sizeof path) return 0;\n'
         '    strcpy(cut + 1, "astralchain.ini");',
         '    if (!cut || (size_t)(path + sizeof path - (cut + 1)) < sizeof "newsnap.ini") return 0;\n'
         '    strcpy(cut + 1, "newsnap.ini");'),
        ('''static void load_ini(void) {
    if (!find_ini()) return;
    if (!cfg_load(ini_path)) {
        rt_log("cfg: no settings file at %s", ini_path);
        return;
    }
    rt_log("cfg: read %s: %d keys", ini_path, n_entries);''',
         '''static void load_ini(void) {
    if (!find_ini()) return;
    const char *load_path = ini_path;
    snap_legacy_ini[0] = snap_primary_ini[0] = 0;
    // Existence, not parse/read success, decides precedence. Never mask a broken new file.
    if (!plat_file_exists(ini_path)) {
        snprintf(snap_legacy_ini, sizeof snap_legacy_ini, "%s", ini_path);
        char *cut = plat_last_sep(snap_legacy_ini);
        if (!cut) cut = strrchr(snap_legacy_ini, '/');
        if (cut && (size_t)(snap_legacy_ini + sizeof snap_legacy_ini - (cut + 1)) >= sizeof "astralchain.ini") {
            strcpy(cut + 1, "astralchain.ini");
            if (plat_file_exists(snap_legacy_ini)) load_path = snap_legacy_ini;
        }
    }
    if (!cfg_load(load_path)) {
        rt_log("cfg: no settings file at %s", load_path);
        return;
    }
    if (load_path == snap_legacy_ini)
        snprintf(snap_primary_ini, sizeof snap_primary_ini, "%s", ini_path);
    rt_log("cfg: read %s: %d keys", load_path, n_entries);'''),
        ('''    uint8_t *data = plat_file_read(path, &size);
    if (!data && plat_file_exists(path) && plat_file_size(path) != 0) {''',
         '''    uint8_t *data = plat_file_read(path, &size);
    // Save only to the new name, preserving all untouched legacy lines as the base.
    if (!data && !plat_file_exists(path) && snap_primary_ini[0] && !strcmp(path, snap_primary_ini)) {
        data = plat_file_read(snap_legacy_ini, &size);
        if (!data) {
            rt_log("cfg: cannot read legacy settings %s, nothing written", snap_legacy_ini);
            __atomic_store_n(&save_ok, 0, __ATOMIC_RELEASE);
            plat_mutex_unlock(&set_lock);
            return 0;
        }
    }
    if (!data && plat_file_exists(path) && plat_file_size(path) != 0) {'''),
    ])
    return changes


def _visible_edits():
    return {'runtime/main.c': [('            if (i > 1) snprintf(from, sizeof from, "%s/totk.%d.log", dir, i - 1);',
                     '            if (i > 1) snprintf(from, sizeof from, "%s/newsnap.%d.log", dir, i - 1);'),
                    ('            else snprintf(from, sizeof from, "%s/astralchain.log", dir);',
                     '            else snprintf(from, sizeof from, "%s/newsnap.log", dir);'),
                    ('            snprintf(to, sizeof to, "%s/totk.%d.log", dir, i);',
                     '            snprintf(to, sizeof to, "%s/newsnap.%d.log", dir, i);'),
                    ('        snprintf(g_log_path, sizeof g_log_path, "%s/astralchain.log", dir);',
                     '        snprintf(g_log_path, sizeof g_log_path, "%s/newsnap.log", dir);'),
                    ('    rt_logf("FATAL: %s (%#x) at host %p (astralchain+%#llx)", x->what, x->code, (void '
                     '*)rip, (unsigned long long)x->offset);',
                     '    rt_logf("FATAL: %s (%#x) at host %p (newsnap+%#llx)", x->what, x->code, (void '
                     '*)rip, (unsigned long long)x->offset);'),
                    ('        rt_logf("  host frame %2d: astralchain+%#llx", i, (unsigned long '
                     'long)(x->frames[i] - (rip - x->offset)));',
                     '        rt_logf("  host frame %2d: newsnap+%#llx", i, (unsigned long '
                     'long)(x->frames[i] - (rip - x->offset)));')],
 'runtime/vk_dlaa.c': [('    rt_log("dlaa: NGX up; DLSS %s%s", avail ? "available" : "NOT available (is '
                        'nvngx_dlss.dll next to astralchain.exe?)",',
                        '    rt_log("dlaa: NGX up; DLSS %s%s", avail ? "available" : "NOT available (is '
                        'nvngx_dlss.dll next to newsnap.exe?)",')],
 'runtime/resolution.c': [('                   !strcmp(up, "dlss") ? "nvngx_dlss.dll from NVIDIA is not next '
                           'to astralchain.exe"',
                           '                   !strcmp(up, "dlss") ? "nvngx_dlss.dll from NVIDIA is not next '
                           'to newsnap.exe"'),
                          ('                   : !strcmp(up, "xess") ? "libxess.dll is not next to '
                           'astralchain.exe"',
                           '                   : !strcmp(up, "xess") ? "libxess.dll is not next to '
                           'newsnap.exe"')],
 'runtime/romfs.c': [('    if (!index_bytes) rt_fatal("RomFS index %s missing (tools/build_game.py writes it '
                      'next to totk.exe)", path);',
                      '    if (!index_bytes) rt_fatal("RomFS index %s missing (tools/build_game.py writes it '
                      'next to newsnap.exe)", path);'),
                     ('    if (!image) rt_fatal("RomFS image %s missing; put romfs.bin into the romfs folder '
                      'next to totk or set AC_ROMFS",',
                      '    if (!image) rt_fatal("RomFS image %s missing; put romfs.bin into the romfs folder '
                      'next to newsnap or set AC_ROMFS",')],
 'runtime/vk_pipeline.c': [('               "astralchain.exe --prepare-shaders in it on this machine", '
                            '(unsigned long long)LB.noshader, LB.n);',
                            '               "newsnap.exe --prepare-shaders in it on this machine", (unsigned '
                            'long long)LB.noshader, LB.n);')],
 'runtime/gfx_window_sdl.c': [('    SDL_SetHint(SDL_HINT_APP_ID, "astralchain");   // Wayland\'s app id: the '
                               'desktop file and the taskbar match it',
                               '    SDL_SetHint(SDL_HINT_APP_ID, "newsnap");   // Wayland\'s app id: the '
                               'desktop file and the taskbar match it')],
 'runtime/platform/linux.c': [('                         "Astral Chain is running", "astralchain") >= 0)',
                               '                         "NewSnapRecomp is running", "newsnap") >= 0)')],
 'runtime/flight.c': [('    fprintf(f, "# astralchain flight dump: %s at frame %llu, interval %.1f ms\\n", '
                       'j->why, (unsigned long long)j->trig_frame,',
                       '    fprintf(f, "# newsnap flight dump: %s at frame %llu, interval %.1f ms\\n", '
                       'j->why, (unsigned long long)j->trig_frame,')],
 'runtime/prof_win.c': [('        fprintf(f, "astralchain-prof 1\\nbase %llx\\nperiod_us 1000\\nframe %llu '
                         'interval_ms %.1f\\nmain %u render %u replay %u\\n",',
                         '        fprintf(f, "newsnap-prof 1\\nbase %llx\\nperiod_us 1000\\nframe %llu '
                         'interval_ms %.1f\\nmain %u render %u replay %u\\n",'),
                        ('    fprintf(f, "astralchain-prof 1\\nbase %llx\\nperiod_us 1000\\nsamples '
                         '%llu\\ndropped %llu\\n", (unsigned long long)(uintptr_t)GetModuleHandleW(NULL),',
                         '    fprintf(f, "newsnap-prof 1\\nbase %llx\\nperiod_us 1000\\nsamples '
                         '%llu\\ndropped %llu\\n", (unsigned long long)(uintptr_t)GetModuleHandleW(NULL),')],
 'runtime/kernel.c': [('                   "astralchain.ini to play");',
                       '                   "newsnap.ini to play");'),
                      ('               "astralchain.ini before reporting this crash");',
                       '               "newsnap.ini before reporting this crash");')],
 'runtime/ui_text.c': [('                               "RTX GPU and nvngx_dlss.dll next to astralchain.exe, '
                        'Intel XeSS a recent GPU and "',
                        '                               "RTX GPU and nvngx_dlss.dll next to newsnap.exe, '
                        'Intel XeSS a recent GPU and "'),
                       ('                               "libxess.dll next to astralchain.exe; AMD FSR 3 runs '
                        'on any GPU. Automatic takes DLSS "',
                        '                               "libxess.dll next to newsnap.exe; AMD FSR 3 runs on '
                        'any GPU. Automatic takes DLSS "'),
                       ('                               "nvngx_dlss.dll рядом с astralchain.exe, Intel XeSS '
                        '— современная видеокарта и libxess.dll "',
                        '                               "nvngx_dlss.dll рядом с newsnap.exe, Intel XeSS — '
                        'современная видеокарта и libxess.dll "'),
                       ('                               "рядом с astralchain.exe; AMD FSR 3 работает на '
                        'любой видеокарте. «Автоматически» берёт "',
                        '                               "рядом с newsnap.exe; AMD FSR 3 работает на любой '
                        'видеокарте. «Автоматически» берёт "'),
                       ('                               "de uma placa NVIDIA RTX e do nvngx_dlss.dll ao lado '
                        'do astralchain.exe, Intel XeSS de uma "',
                        '                               "de uma placa NVIDIA RTX e do nvngx_dlss.dll ao lado '
                        'do newsnap.exe, Intel XeSS de uma "'),
                       ('                               "placa recente e do libxess.dll ao lado do '
                        'astralchain.exe; AMD FSR 3 roda em qualquer "',
                        '                               "placa recente e do libxess.dll ao lado do '
                        'newsnap.exe; AMD FSR 3 roda em qualquer "'),
                       ('                               "NVIDIA DLSS 需要 NVIDIA RTX 显卡，并将 nvngx_dlss.dll 放在 '
                        'astralchain.exe 旁；Intel XeSS "',
                        '                               "NVIDIA DLSS 需要 NVIDIA RTX 显卡，并将 nvngx_dlss.dll 放在 '
                        'newsnap.exe 旁；Intel XeSS "'),
                       ('                               "需要较新的显卡，并将 libxess.dll 放在 astralchain.exe 旁；AMD FSR '
                        '3 可在任何显卡上运行。"',
                        '                               "需要较新的显卡，并将 libxess.dll 放在 newsnap.exe 旁；AMD FSR 3 '
                        '可在任何显卡上运行。"')],
 'runtime/cfg.c': [('    if (!is_known(key)) rt_log("cfg: astralchain.ini line %d: unknown key \'%s\'", '
                    'line, key);',
                    '    if (!is_known(key)) rt_log("cfg: newsnap.ini line %d: unknown key \'%s\'", line, '
                    'key);'),
                   ('    rt_log("cfg: astralchain.ini ssaa = %s is read as output_res = %s", v, to);',
                    '    rt_log("cfg: newsnap.ini ssaa = %s is read as output_res = %s", v, to);'),
                   ('    rt_log("cfg: astralchain.ini %s = 1 is read as anti_aliasing = %s", to, to);',
                    '    rt_log("cfg: newsnap.ini %s = 1 is read as anti_aliasing = %s", to, to);'),
                   ('        rt_log("cfg: astralchain.ini dlss = %s is no longer read: upscaling_quality '
                    'sets the upscaler\'s mode", dlss->value);',
                    '        rt_log("cfg: newsnap.ini dlss = %s is no longer read: upscaling_quality sets '
                    'the upscaler\'s mode", dlss->value);'),
                   ('        rt_log("cfg: astralchain.ini anti_aliasing = %s is read as upscaling = %s, '
                    'upscaling_quality = native and "',
                    '        rt_log("cfg: newsnap.ini anti_aliasing = %s is read as upscaling = %s, '
                    'upscaling_quality = native and "'),
                   ('        rt_log("cfg: astralchain.ini anti_aliasing = %s is read as anti_aliasing = '
                    'smaa", old);',
                    '        rt_log("cfg: newsnap.ini anti_aliasing = %s is read as anti_aliasing = smaa", '
                    'old);'),
                   ('    rt_log("cfg: astralchain.ini pad_layout = xbox_prompts is read as pad_layout = '
                    'nintendo and prompts = %s",',
                    '    rt_log("cfg: newsnap.ini pad_layout = xbox_prompts is read as pad_layout = nintendo '
                    'and prompts = %s",'),
                   ('            if (!eq) rt_log("cfg: astralchain.ini line %d: no \'=\' in \'%s\'", line, '
                    's);',
                    '            if (!eq) rt_log("cfg: newsnap.ini line %d: no \'=\' in \'%s\'", line, s);'),
                   ('        if (!o->buf) rt_fatal("cfg: out of memory writing astralchain.ini");',
                    '        if (!o->buf) rt_fatal("cfg: out of memory writing newsnap.ini");'),
                   ('    if (!lines || !replace || !after_key || !drop) rt_fatal("cfg: out of memory writing '
                    'astralchain.ini");',
                    '    if (!lines || !replace || !after_key || !drop) rt_fatal("cfg: out of memory writing '
                    'newsnap.ini");'),
                   ('        if (getenv(var)) rt_log("cfg: %s is set in the environment and overrides '
                    'astralchain.ini", var);',
                    '        if (getenv(var)) rt_log("cfg: %s is set in the environment and overrides '
                    'newsnap.ini", var);'),
                   ('        rt_log("cfg: Steam Deck: astralchain.ini output_res = %s renders 1920x1080, '
                    'more than the 1280x800 screen shows; "',
                    '        rt_log("cfg: Steam Deck: newsnap.ini output_res = %s renders 1920x1080, more '
                    'than the 1280x800 screen shows; "'),
                   ('        rt_log("cfg: astralchain.ini aspect = %s dates from before the wide view; '
                    'removed once so the default, wide, "',
                    '        rt_log("cfg: newsnap.ini aspect = %s dates from before the wide view; removed '
                    'once so the default, wide, "'),
                   ('        rt_log("cfg: device profile Steam Deck: defaults for the keys astralchain.ini '
                    'does not set (AC_DEVICE_PROFILE=desktop "',
                    '        rt_log("cfg: device profile Steam Deck: defaults for the keys newsnap.ini does '
                    'not set (AC_DEVICE_PROFILE=desktop "')]}
