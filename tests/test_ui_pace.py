"""UI-HZ-01: interface timelines step at 60 a second of real time above 60 fps."""
import os
import shutil
from pathlib import Path
import subprocess
import tempfile
import unittest

from newsnap.ui_pace_adapt import edits
from newsnap.upstream import ROOT, UPSTREAM


class UiPaceTests(unittest.TestCase):
    def compiler(self):
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang')
        if not compiler:
            self.skipTest('clang is required for native pacing fixtures')
        return compiler

    def test_patch_set_is_registered_and_names_the_four_verified_sites(self):
        text = (ROOT / 'patches/snap-2.0.1-ui-pace.txt').read_text(encoding='utf-8')
        lines = [line.split() for line in text.splitlines() if line and not line.startswith('#')]
        # off by default: 0.9.3 shipped it on and it broke the interface above 60 fps
        self.assertEqual(lines[0], ['set', 'snap_ui_pace', 'AC_SNAP_UI_PACE_PATCH', '0'])
        # helper before the original load at the two walk starts, after it at the two movie loads
        self.assertEqual(lines[1:], [
            ['site', 'snap_ui_pace', 'main', '7838e4', 'f94072c8', '@fn:snap_ui_pace_begin', 'f94072c8'],
            ['site', 'snap_ui_pace', 'main', '7838f8', 'f9400a80', 'f9400a80', '@fn:snap_ui_pace_movie'],
            ['site', 'snap_ui_pace', 'main', '790de8', 'f9407108', '@fn:snap_ui_pace_begin', 'f9407108'],
            ['site', 'snap_ui_pace', 'main', '790dfc', 'f9400aa0', 'f9400aa0', '@fn:snap_ui_pace_movie'],
        ])
        self.assertIn("'snap-2.0.1-ui-pace.txt'", (ROOT / 'newsnap/build.py').read_text(encoding='utf-8'))

    def test_helpers_are_declared_for_the_patch_table(self):
        source = (UPSTREAM / 'runtime/cpu.h').read_text(encoding='utf-8')
        for old, _new in edits()['runtime/cpu.h']:
            self.assertEqual(source.count(old), 1)
        declared = ''.join(new for _old, new in edits()['runtime/cpu.h'])
        self.assertIn('ui_pace_edits', (ROOT / 'newsnap/adapt.py').read_text(encoding='utf-8'))
        self.assertIn('void snap_ui_pace_begin(Cpu *c);', declared)
        self.assertIn('void snap_ui_pace_movie(Cpu *c);', declared)

    def test_decision_keeps_sixty_steps_a_second_at_any_rate(self):
        compiler = self.compiler()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / 'fixture.c').write_text(r'''
#include <stdio.h>
#include "snap_ui_pace.h"
// Steps taken over `seconds` at a steady frame period, with `walks` lookups per frame.
static unsigned run(uint64_t period, unsigned seconds, unsigned walks, uint64_t cap) {
    SnapUiPace p = {0, 0, 0, 1};
    unsigned steps = 0;
    uint64_t now = 1000, frames = seconds * 1000000000ull / period;
    for (uint64_t f = 0; f < frames; f++, now += period) {
        int first = snap_ui_pace_decide(&p, f, now, cap);
        for (unsigned w = 1; w < walks; w++)
            if (snap_ui_pace_decide(&p, f, now + w * 300000, cap) != first) return 99999;   // one answer a frame
        steps += (unsigned)first;
    }
    return steps;
}
int main(void) {
    const unsigned rates[] = {72, 90, 100, 120, 144, 165, 240};
    for (unsigned i = 0; i < sizeof rates / sizeof *rates; i++) {
        uint64_t period = 1000000000ull / rates[i];
        unsigned steps = run(period, 10, 13, period);
        if (steps < 598 || steps > 601) { printf("rate %u: %u steps\n", rates[i], steps); return 1; }
    }
    // 60 fps and below: every frame steps, as the game does, even with jitter around the period
    if (run(16666667, 10, 3, 16666667) != 10 * 1000000000ull / 16666667) return 2;   // every frame
    if (run(33333333, 10, 3, 33333333) != 10 * 1000000000ull / 33333333) return 3;
    { SnapUiPace p = {0, 0, 0, 1}; uint64_t now = 5; unsigned steps = 0;
      for (unsigned f = 0; f < 600; f++) { now += f % 2 ? 15900000 : 17400000; steps += (unsigned)snap_ui_pace_decide(&p, f, now, 16666667); }
      if (steps != 600) return 4; }
    // a hitch never banks steps: after a 2 s stall at 144 fps the next frames step at most once each
    { SnapUiPace p = {0, 0, 0, 1}; uint64_t now = 5, period = 6944444; unsigned f = 0, burst = 0;
      for (; f < 144; f++, now += period) snap_ui_pace_decide(&p, f, now, period);
      now += 2000000000ull;
      for (unsigned k = 0; k < 4; k++, f++, now += period) burst += (unsigned)snap_ui_pace_decide(&p, f, now, period);
      if (burst > 3) return 5; }
    // unknown period (0) and the first frame step
    { SnapUiPace p = {0, 0, 0, 1}; if (!snap_ui_pace_decide(&p, 7, 100, 0)) return 6; }
    return 0;
}
''')
            exe = p / 'pace.exe'
            subprocess.run([compiler, str(p / 'fixture.c'), '-I', str(ROOT / 'newsnap/overlays'), '-o', str(exe)],
                           check=True, capture_output=True)
            result = subprocess.run([str(exe)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_helpers_touch_only_x0_and_only_on_held_frames(self):
        compiler = self.compiler()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / 'cpu.h').write_text('#include <stdint.h>\ntypedef struct {uint64_t x[32],sp,pc,nzcv; char rest[1024];} Cpu;\n')
            (p / 'host.h').write_text('#include <stdint.h>\nuint64_t kern_now_ns(void); uint64_t frame_step_cap_ns(void);'
                                      ' void rt_log(const char *,...);\n')
            (p / 'gfx.h').write_text('#include <stdint.h>\ntypedef struct { uint64_t frames; } GfxStats;\n')
            (p / 'fixture.c').write_text(r'''
#include <string.h>
#include "cpu.h"
#include "gfx.h"
GfxStats gfx_counters;
static uint64_t now = 1000, cap = 6944444;
uint64_t kern_now_ns(void) { return now; }
uint64_t frame_step_cap_ns(void) { return cap; }
void rt_log(const char *f, ...) { (void)f; }
void snap_ui_pace_begin(Cpu *);
void snap_ui_pace_movie(Cpu *);
int main(void) {
    Cpu c, before;
    unsigned held = 0, stepped = 0;
    uint64_t movie[2] = {0, 0};
    for (unsigned f = 0; f < 1440; f++, now += cap, gfx_counters.frames++) {
        memset(&c, 0x5a, sizeof c);
        before = c;
        snap_ui_pace_begin(&c);
        if (memcmp(&c, &before, sizeof c)) return 1;                 // the walk start changes nothing
        c.x[0] = (uint64_t)(uintptr_t)movie;
        before = c;
        snap_ui_pace_movie(&c);
        uint64_t x0 = c.x[0];
        c.x[0] = before.x[0];
        if (memcmp(&c, &before, sizeof c)) return 2;                 // nothing besides x0
        if (x0 == (uint64_t)(uintptr_t)movie) { stepped++; continue; }
        // the stand-in: movie[+8] -> owner, owner[+0x38] == 0, which the player's first check rejects
        const uint64_t *stand_in = (const uint64_t *)(uintptr_t)x0, *owner = (const uint64_t *)(uintptr_t)stand_in[1];
        if (!owner || owner[7]) return 3;
        held++;
    }
    return stepped >= 598 && stepped <= 601 && held == 1440 - stepped ? 0 : 4;
}
''')
            exe = p / 'helpers.exe'
            subprocess.run([compiler, str(p / 'fixture.c'), str(ROOT / 'newsnap/overlays/snap_ui_pace.c'), '-I', str(p),
                            '-I', str(ROOT / 'newsnap/overlays'), '-o', str(exe)], check=True, capture_output=True)
            result = subprocess.run([str(exe)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
