"""PRESENT-WIN-01: smooth presentation in a window when the driver offers no mailbox.

AMD's Windows driver lists immediate, FIFO and FIFO relaxed but no mailbox (owner's
RX 6900 XT: modes 0, 2, 3). The launcher asks for mailbox, so the runtime fell back
to FIFO. Over the whole monitor (the runtime's borderless fullscreen) that paces
cleanly: 16.7 ms frames, at most 18 ms, on the owner's machine. In a window that
does not cover the monitor, the desktop compositor (DWM) presents it, and FIFO then
blocks to the compositor's rhythm: the game's presents came in pairs, about 1500
of 3600 frames a minute over 25 ms. A composited window cannot tear (the compositor
always shows a whole image), so immediate there behaves like mailbox.

When mailbox was asked for and is missing, a window smaller than its monitor gets
immediate; borderless/fullscreen keeps FIFO. The swapchain is recreated on every
size or fullscreen change, so the choice follows the window. AC_WINDOWED_IMMEDIATE=0
keeps FIFO everywhere. Any GPU vendor without mailbox.
"""

BEFORE = '    for (uint32_t i = 0; i < n; i++) if (m[i] == want) got = want;\n'

AFTER = BEFORE + '''    // NewSnap PRESENT-WIN-01: mailbox asked for but missing (AMD's Windows driver). A window smaller than its monitor is
    // composited by the desktop, where FIFO blocks to the compositor's rhythm and presents come in pairs, and where an
    // immediate present cannot tear: take immediate there. Over the whole monitor FIFO stays (it paces cleanly).
    if (want == VK_PRESENT_MODE_MAILBOX_KHR && got != want && rt_knob("WINDOWED_IMMEDIATE", "1")) {
        int cw = 0, ch = 0, mw = 0, mh = 0;
        wsys_client_size(&cw, &ch);
        if (gfx_window_monitor_size(&mw, &mh) && cw > 0 && ch > 0 && (cw < mw || ch < mh))
            for (uint32_t i = 0; i < n; i++)
                if (m[i] == VK_PRESENT_MODE_IMMEDIATE_KHR) got = m[i];
    }
'''


def edits():
    return {'runtime/gfx_present.c': [
        ('#include "vk.h"\n', '#include "vk.h"\n\nint gfx_window_monitor_size(int *w, int *h);   // gfx_window_win.c / gfx_window_sdl.c\n'),
        (BEFORE, AFTER),
    ], 'runtime/cfg.c': [
        ('"WALK_KEY", "WALK_SCALE", "WB_EXACT",', '"WALK_KEY", "WALK_SCALE", "WB_EXACT", "WINDOWED_IMMEDIATE",'),
    ]}
