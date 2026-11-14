// ULTRAWIDE-01 (AC_ASPECT=ultrawide): Snap keeps its 16:9 render targets; the present stretches the picture to the
// window (gfx_fit_rect) and 16:9 perspective cameras get the window's ratio where their projection is built, so the
// stretched picture shows a wider view with the game's proportions. Same approach as Astral Chain's "wide" set
// (third_party/astral/recomp/patches-v101.txt, from TLin-Y's aspect-ratio pchtxt): wider lens, same targets.
//
// main+0x29641c, in the perspective builder (0x296400: fdiv s2,s12,s0 = cot(fov/2); 0x296418: fdiv s1,s2,s9 with
// s9 = the camera's aspect, [x20,#0x12c]): s1 is the X scale. Only a 16:9 camera is widened; the photo/evaluation
// cameras and any other ratio keep theirs, so captured photos and scoring do not change.
#include <math.h>
#include <string.h>
#include "cpu.h"
#include "simd.h"
#include "cfg.h"

static volatile float snap_wide_ratio;   // the swapchain's width / height (gfx_present.c, res_wide_window)

void snap_wide_window(unsigned w, unsigned h) {
    if (h) snap_wide_ratio = (float)w / (float)h;
}

int snap_aspect_fills(const char *aspect) {
    return aspect && (!strcmp(aspect, "stretch") || !strcmp(aspect, "ultrawide"));
}

void snap_wide_proj_s1(Cpu *c) {
    const float base = 16.0f / 9.0f, r = snap_wide_ratio;
    if (!(r > base * 1.01f && r <= 4.0f) || strcmp(cfg_value("AC_ASPECT"), "ultrawide")) return;
    float aspect = VSF32(9);
    if (fabsf(aspect - base) > 0.002f) return;
    FP_SETS(1, VSF32(1) * aspect / r);
}
