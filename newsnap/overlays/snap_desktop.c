// MENU-02: helpers for the window default and the performance overlay.
// - AC_WINDOW_SIZE=auto (the default): the window takes the desktop's size, so borderless fullscreen and the window
//   start at the monitor's resolution (2560x1440 on a 1440p desktop).
// - The overlay's scene line shows the 3D size after the host's internal-resolution scale (snap_output_scale.h).
#include <stdint.h>
#include "snap_output_scale.h"
#ifdef _WIN32
#include <windows.h>
int snap_desktop_size(int *w, int *h) {
    int x = GetSystemMetrics(SM_CXSCREEN), y = GetSystemMetrics(SM_CYSCREEN);
    if (x < 640 || y < 360) return 0;
    *w = x, *h = y;
    return 1;
}
#else
int snap_desktop_size(int *w, int *h) { (void)w, (void)h; return 0; }
#endif

float snap_scene_scale(void) { return snap_host_scale_factor(); }
