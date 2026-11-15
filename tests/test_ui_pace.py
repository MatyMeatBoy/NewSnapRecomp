"""UI-HZ-01: the interface handler's logic, timelines and per-frame event step 60 times a second above 60 fps."""
import os
import shutil
from pathlib import Path
import subprocess
import tempfile
import unittest

from newsnap.ui_pace_adapt import edits
from newsnap.upstream import ROOT, UPSTREAM


def cbz_x16(site, target):
    return '%08x' % (0xB4000000 | (((target - site) // 4) & 0x7ffff) << 5 | 16)


class UiPaceTests(unittest.TestCase):
    def compiler(self):
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang')
        if not compiler:
            self.skipTest('clang is required for native pacing fixtures')
        return compiler

    def test_patch_set_is_registered_and_branches_to_the_drawing_section_and_the_exit(self):
        text = (ROOT / 'patches/snap-2.0.1-ui-pace.txt').read_text(encoding='utf-8')
        lines = [line.split() for line in text.splitlines() if line and not line.startswith('#')]
        self.assertEqual(lines[0], ['set', 'snap_ui_pace', 'AC_SNAP_UI_PACE_PATCH', '1'])
        # each site: the original instruction, the helper, then cbz x16 to the handler's own label
        self.assertEqual(lines[1:], [
            ['site', 'snap_ui_pace', 'main', '783610', 'f900c7e0', 'f900c7e0', '@fn:snap_ui_pace_enter',
             cbz_x16(0x783610, 0x794b4c)],
            ['site', 'snap_ui_pace', 'main', '794b90', 'f940c7e0', 'f940c7e0', '@fn:snap_ui_pace_event',
             cbz_x16(0x794b90, 0x795f08)],
            # INPUT-HZ-01: the pad update's epilogue, the helper then the original load
            ['site', 'snap_ui_pace', 'main', '9263ac', 'a95b7bfd', '@fn:snap_ui_pace_pad', 'a95b7bfd'],
        ])
        self.assertIn("'snap-2.0.1-ui-pace.txt'", (ROOT / 'newsnap/build.py').read_text(encoding='utf-8'))

    def test_helpers_are_declared_for_the_patch_table(self):
        source = (UPSTREAM / 'runtime/cpu.h').read_text(encoding='utf-8')
        for old, _new in edits()['runtime/cpu.h']:
            self.assertEqual(source.count(old), 1)
        declared = ''.join(new for _old, new in edits()['runtime/cpu.h'])
        self.assertIn('ui_pace_edits', (ROOT / 'newsnap/adapt.py').read_text(encoding='utf-8'))
        self.assertIn('void snap_ui_pace_enter(Cpu *c);', declared)
        self.assertIn('void snap_ui_pace_event(Cpu *c);', declared)
        self.assertIn('void snap_ui_pace_pad(Cpu *c);', declared)

    def test_decision_keeps_sixty_steps_a_second_at_any_rate(self):
        compiler = self.compiler()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / 'fixture.c').write_text(r'''
#include <stdio.h>
#include "snap_ui_pace.h"
// Steps taken over `seconds` at a steady frame period, with `lookups` decisions asked per frame.
static unsigned run(uint64_t period, unsigned seconds, unsigned lookups, uint64_t cap) {
    SnapUiPace p = {0, 0, 0, 1};
    unsigned steps = 0;
    uint64_t now = 1000, frames = seconds * 1000000000ull / period;
    for (uint64_t f = 0; f < frames; f++, now += period) {
        int first = snap_ui_pace_decide(&p, f, now, cap);
        for (unsigned w = 1; w < lookups; w++)
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
    if (run(16666667, 10, 3, 16666667) != 10 * 1000000000ull / 16666667) return 2;
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

    def test_helpers_set_only_the_scratch_register_and_respect_the_handler_state(self):
        compiler = self.compiler()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / 'platform').mkdir()
            (p / 'cpu.h').write_text('#include <stdint.h>\ntypedef struct {uint64_t x[32],sp,pc,nzcv; char rest[1024];} Cpu;\n')
            (p / 'host.h').write_text('#include <stdint.h>\nuint64_t kern_now_ns(void); uint64_t frame_step_cap_ns(void);'
                                      ' void rt_log(const char *,...);\n')
            (p / 'gfx.h').write_text('#include <stdint.h>\ntypedef struct { uint64_t frames; } GfxStats;\n')
            (p / 'platform/platform.h').write_text('#include <stddef.h>\n#include <stdint.h>\nint plat_mem_read(uint64_t,void *,size_t);\n')
            (p / 'fixture.c').write_text(r'''
#include <string.h>
#include "cpu.h"
#include "gfx.h"
GfxStats gfx_counters;
static uint64_t now = 1000, cap = 6944444;
static int readable = 1;
uint64_t kern_now_ns(void) { return now; }
uint64_t frame_step_cap_ns(void) { return cap; }
void rt_log(const char *f, ...) { (void)f; }
int plat_mem_read(uint64_t a, void *out, size_t n) { if (!readable) return 0; memcpy(out, (void *)(uintptr_t)a, n); return 1; }
void snap_ui_pace_enter(Cpu *);
void snap_ui_pace_event(Cpu *);
// One helper call; fails unless only x16 changed and the object's bytes stayed as they were.
static int call(void (*fn)(Cpu *), unsigned char *object, uint64_t *x16) {
    Cpu c, before;
    unsigned char saved[0x100];
    memset(&c, 0x5a, sizeof c);
    c.x[0] = (uint64_t)(uintptr_t)object;
    before = c;
    if (object) memcpy(saved, object, sizeof saved);
    fn(&c);
    *x16 = c.x[16];
    c.x[16] = before.x[16];
    if (memcmp(&c, &before, sizeof c)) return 0;
    return !object || !memcmp(saved, object, sizeof saved);
}
int main(void) {
    unsigned char object[0x100] = {0};
    object[0xc0] = 1, object[0xc6] = 1;                 // started and ready, not held: the shortcut applies
    unsigned run = 0, draw_only = 0, raised = 0;
    uint64_t x16;
    for (unsigned f = 0; f < 1440; f++, now += cap, gfx_counters.frames++) {
        if (!call(snap_ui_pace_enter, object, &x16) || x16 > 1) return 1;
        run += (unsigned)x16, draw_only += !x16;
        uint64_t enter = x16;
        if (!call(snap_ui_pace_event, object, &x16) || x16 != enter) return 2;   // the event follows the same frame
        raised += (unsigned)x16;
    }
    if (run < 598 || run > 601 || draw_only != 1440 - run || raised != run) return 3;
    // on a frame that is not due, an object the handler would not carry on with takes the original path
    for (unsigned f = 0; f < 6; f++, now += cap, gfx_counters.frames++) {
        uint64_t normal, a, b, d, e;
        if (!call(snap_ui_pace_enter, object, &normal)) return 4;
        if (normal) continue;                                           // a due frame: nothing to compare
        object[0xc0] = 0; if (!call(snap_ui_pace_enter, object, &a)) return 5; object[0xc0] = 1;   // not started
        object[0xc6] = 0; if (!call(snap_ui_pace_enter, object, &b)) return 5; object[0xc6] = 1;   // not ready
        object[0xc4] = 1; if (!call(snap_ui_pace_enter, object, &d)) return 5; object[0xc4] = 0;   // held by the game
        readable = 0;     if (!call(snap_ui_pace_enter, object, &e)) return 5; readable = 1;       // unreadable object
        if (!a || !b || !d || !e) return 6;
        uint64_t none;
        if (!call(snap_ui_pace_enter, 0, &none) || !none) return 7;      // null object
        return 0;
    }
    return 8;
}
''')
            exe = p / 'helpers.exe'
            subprocess.run([compiler, str(p / 'fixture.c'), str(ROOT / 'newsnap/overlays/snap_ui_pace.c'), '-I', str(p),
                            '-I', str(ROOT / 'newsnap/overlays'), '-o', str(exe)], check=True, capture_output=True)
            result = subprocess.run([str(exe)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
