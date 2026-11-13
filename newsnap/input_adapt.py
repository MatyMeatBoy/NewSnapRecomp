"""Small Snap input changes over the pinned, unmodified host runtime."""


def edits():
    """Return exact-once source seams for adapt_sources to stage."""
    return {
        'runtime/input_map.c': [
            ('{KEY_MOUSE_L, B_Y}, {KEY_MOUSE_R, B_ZL}',
             '{KEY_MOUSE_L, B_A}, {KEY_MOUSE_R, B_ZL}'),
        ],
        'runtime/input.c': [
            ('#include "input_wsys.h"',
             '#include "input_wsys.h"\n#include "snap_input_trace.h"\n#include "snap_controller_db.h"'),
            ('    if (state == 1) test_pad_attach();',
             '    if (state == 1) snap_controller_db_load();\n    if (state == 1) test_pad_attach();'),
            ('    SDL_UpdateGamepads();\n    int n = 0, kind = PAD_KIND_NONE;',
             '    snap_controller_db_load();\n    SDL_UpdateGamepads();\n    int n = 0, kind = PAD_KIND_NONE;'),
            ('            input_mouse_stick(dx, dy, dt, mouse_sens_get(), held);',
             '''            input_mouse_stick(dx, dy, dt, mouse_sens_get(), held);
            snap_input_trace(0, fr, dx, dy, held[0], held[1], 0);'''),
            ('    rec_apply(b, sl, sr);',
             '''    rec_apply(b, sl, sr);
    snap_input_trace(1, __atomic_load_n(&gfx_counters.frames, __ATOMIC_RELAXED),
                     sl[0], sl[1], sr[0], sr[1], b);'''),
        ],
    }
