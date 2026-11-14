"""ULTRAWIDE-01: AC_ASPECT=ultrawide stretches the 16:9 picture and widens 16:9 cameras (snap_wide.c)."""


def edits():
    return {
        'runtime/cpu.h': [
            ('typedef void (*GuestFn)(Cpu *);', 'void snap_wide_proj_s1(Cpu *c);\ntypedef void (*GuestFn)(Cpu *);'),
        ],
        'runtime/cfg.c': [
            ('{"ASPECT", "fit", "fit|stretch", LIVE}', '{"ASPECT", "fit", "fit|stretch|ultrawide", LIVE}'),
        ],
        'runtime/gfx_present.c': [
            ('static float g_shape;', 'static float g_shape;\nvoid snap_wide_window(unsigned w, unsigned h);\nint snap_aspect_fills(const char *aspect);'),
            ('!strcmp(cfg_value("AC_ASPECT"), "stretch")) return;', 'snap_aspect_fills(cfg_value("AC_ASPECT"))) return;'),
            ('    res_wide_window(ext.width, ext.height);', '    res_wide_window(ext.width, ext.height);\n    snap_wide_window(ext.width, ext.height);'),
        ],
    }
