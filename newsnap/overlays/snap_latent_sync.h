// PACE-AMD-01: with AC_FPS=display (snap_high_fps.h: the cap is an exact fraction of the refresh rate), move each
// paced present to the middle of its refresh interval, so timer jitter (~0.5 ms) never pushes a frame across a vblank
// and every frame stays on screen for the same number of refreshes under FIFO. Same idea as Special K's Latent Sync
// (present at a chosen scanline phase). The vblank time and period come from DwmGetCompositionTimingInfo (QPC units;
// plat_now_ns is QPC in ns), loaded at run time. Off (unchanged target) for every other frame-rate setting, without
// DWM timing, or for implausible values. VRR displays should keep a normal cap: they show frames as they come.
#pragma once
#include <stdint.h>
#include <string.h>

#ifdef _WIN32
#include <windows.h>
#include <dwmapi.h>   // DWM_TIMING_INFO only; the function is loaded at run time, no import library

static inline int snap_latent_on(const char *fps) { return fps && !strcmp(fps, "display"); }

// Pure part, unit-tested: the time in the middle of the refresh interval nearest to at.
static inline uint64_t snap_vblank_mid_of(uint64_t at, uint64_t vblank_ns, double period_ns) {
    if (!(period_ns > 2e6 && period_ns < 5e7)) return at;
    double k = ((double)at - (double)vblank_ns) / period_ns - 0.5;
    double r = k >= 0 ? (double)(int64_t)(k + 0.5) : -(double)(int64_t)(-k + 0.5);
    double t = (double)vblank_ns + (r + 0.5) * period_ns;
    return t > 0 ? (uint64_t)t : at;
}

static inline uint64_t snap_vblank_mid(uint64_t at, const char *fps) {
    typedef HRESULT (WINAPI *TimingFn)(HWND, DWM_TIMING_INFO *);
    static TimingFn fn;
    static int loaded;
    static double qpc_to_ns;
    if (!at || !snap_latent_on(fps)) return at;
    if (!loaded) {
        loaded = 1;
        HMODULE m = LoadLibraryW(L"dwmapi.dll");
        if (m) fn = (TimingFn)(void *)GetProcAddress(m, "DwmGetCompositionTimingInfo");
        LARGE_INTEGER f;
        if (QueryPerformanceFrequency(&f) && f.QuadPart > 0) qpc_to_ns = 1e9 / (double)f.QuadPart;
    }
    if (!fn || !qpc_to_ns) return at;
    DWM_TIMING_INFO ti;
    memset(&ti, 0, sizeof ti);
    ti.cbSize = sizeof ti;
    if (fn(NULL, &ti) != 0 || !ti.qpcRefreshPeriod || !ti.qpcVBlank) return at;
    return snap_vblank_mid_of(at, (uint64_t)((double)ti.qpcVBlank * qpc_to_ns), (double)ti.qpcRefreshPeriod * qpc_to_ns);
}
#else
static inline uint64_t snap_vblank_mid(uint64_t at, const char *fps) { (void)fps; return at; }
#endif
