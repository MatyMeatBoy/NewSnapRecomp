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
        self.assertEqual(lines[1:5], [
            ['site', 'snap_ui_pace', 'main', '783610', 'f900c7e0', 'f900c7e0', '@fn:snap_ui_pace_enter',
             cbz_x16(0x783610, 0x794b4c)],
            ['site', 'snap_ui_pace', 'main', '794b90', 'f940c7e0', 'f940c7e0', '@fn:snap_ui_pace_event',
             cbz_x16(0x794b90, 0x795f08)],
            # INPUT-HZ-01: the pad update's epilogue, the helper then the original load
            ['site', 'snap_ui_pace', 'main', '9263ac', 'a95b7bfd', '@fn:snap_ui_pace_pad', 'a95b7bfd'],
            # FPS-02: the pointer's frame time, the original load then the helper
            ['site', 'snap_ui_pace', 'main', '643cc8', 'bd401e61', 'bd401e61', '@fn:snap_ui_pace_pointer'],
        ])
        self.assertIn(['site', 'snap_ui_pace', 'main', '644344', '394463e8', '394463e8',
                       '@fn:snap_ui_pointer_hover'], lines)
        # RETICLE-HZ-01: its own switch; a draw-only call goes from the drawing section to the handler's loop over
        # the queued positions and back from the loop's end
        self.assertEqual(lines[5:8], [
            ['set', 'snap_ui_positions', 'AC_SNAP_UI_POSITIONS_PATCH', '1'],
            ['site', 'snap_ui_positions', 'main', '794b4c', 'f940c7f6', 'f940c7f6', '@fn:snap_ui_pace_draw',
             cbz_x16(0x794b4c, 0x78d644)],
            ['site', 'snap_ui_positions', 'main', '78d850', 'f9443118', 'f9443118', '@fn:snap_ui_pace_placed',
             cbz_x16(0x78d850, 0x794b4c)],
        ])
        # observers: the helper then the original instruction, in the observation set
        self.assertEqual([line for line in lines if line[:2] == ['site', 'snap_timer_trace']], [
            ['site', 'snap_timer_trace', 'main', '799570', 'd10103ff', '@fn:snap_ui_pos_ask', 'd10103ff'],
            ['site', 'snap_timer_trace', 'main', '78d808', '91008273', '@fn:snap_ui_pos_apply', '91008273'],
            ['site', 'snap_timer_trace', 'main', '78d68c', 'bd401a60', '@fn:snap_ui_pos_clip_named', 'bd401a60'],
            ['site', 'snap_timer_trace', 'main', '78d7ac', 'bd401a60', '@fn:snap_ui_pos_clip_path', 'bd401a60'],
            ['site', 'snap_timer_trace', 'main', '799950', 'd10183ff', '@fn:snap_ui_size_ask', 'd10183ff'],
            ['site', 'snap_timer_trace', 'main', '799b20', 'd10183ff', '@fn:snap_ui_scale_ask', 'd10183ff'],
            ['site', 'snap_timer_trace', 'main', '7995f0', 'fc1c0fe8', '@fn:snap_ui_rotation_ask', 'fc1c0fe8'],
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
        self.assertIn('void snap_ui_pace_pointer(Cpu *c);', declared)
        for name in ('snap_ui_pace_draw', 'snap_ui_pace_placed', 'snap_ui_pos_ask', 'snap_ui_pos_apply',
                     'snap_ui_pos_clip_named', 'snap_ui_pos_clip_path', 'snap_ui_size_ask', 'snap_ui_scale_ask',
                     'snap_ui_rotation_ask', 'snap_ui_motion_hand'):
            self.assertIn(f'void {name}(Cpu *c);', declared)

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

    def test_hover_does_not_treat_a_frame_without_an_interface_update_as_a_leave(self):
        compiler = self.compiler()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / 'platform').mkdir()
            (p / 'cpu.h').write_text('#include <stdint.h>\ntypedef struct {uint64_t x[32],sp,pc,nzcv; __uint128_t v[32]; char rest[512];} Cpu;\n')
            (p / 'host.h').write_text('#include <stdint.h>\nuint64_t kern_now_ns(void); uint64_t frame_step_cap_ns(void);'
                                      ' void rt_log(const char *,...);\n')
            (p / 'gfx.h').write_text('#include <stdint.h>\ntypedef struct { uint64_t frames; } GfxStats;\n')
            (p / 'platform/platform.h').write_text('#include <stddef.h>\n#include <stdint.h>\nint plat_mem_read(uint64_t,void *,size_t);\n'
                                                   'int plat_mem_readable(uint64_t,uint64_t);\n')
            (p / 'fixture.c').write_text(r'''
#include <string.h>
#include "cpu.h"
#include "gfx.h"
GfxStats gfx_counters;
static uint64_t now=1000, cap=6944444;
uint64_t kern_now_ns(void){return now;}
uint64_t frame_step_cap_ns(void){return cap;}
void rt_log(const char *f,...){(void)f;}
int plat_mem_read(uint64_t a,void *out,size_t n){memcpy(out,(void *)(uintptr_t)a,n);return 1;}
int plat_mem_readable(uint64_t a,uint64_t n){return 1;}
void snap_ui_pace_enter(Cpu *);
void snap_ui_pointer_hover(Cpu *);
int main(void){
 unsigned char object[0x100]={0}; object[0xc0]=object[0xc6]=1;
 unsigned rates[]={60,90,120,144};
 for(unsigned r=0;r<4;r++){
  cap=1000000000ull/rates[r];
  unsigned old=0,transitions=0,skipped=0;
  for(unsigned f=0;f<rates[r]*4;f++,now+=cap,gfx_counters.frames++){
   Cpu c,before; memset(&c,0x5a,sizeof c); c.x[0]=(uint64_t)(uintptr_t)object;
   snap_ui_pace_enter(&c); int step=c.x[16];
   // Captured failure: adapters report a hit on updates and zero on intervening frames.
   unsigned desired=f<rates[r]*2,raw=step?desired:0;
   c.x[8]=raw; c.x[9]=old; before=c;
   snap_ui_pointer_hover(&c);
   unsigned effective=(unsigned)c.x[8];
   c.x[8]=before.x[8];
   if(memcmp(&c,&before,sizeof c)) return 1;
   if(effective!=(step?desired:old)) return 2;
   transitions+=effective!=old; old=effective; skipped+=!step;
  }
  if(transitions!=2 || old || (r && !skipped))return 3;
 }
 return 0;
}
''')
            exe = p / 'hover.exe'
            subprocess.run([compiler, str(p / 'fixture.c'), str(ROOT / 'newsnap/overlays/snap_ui_pace.c'), '-I', str(p),
                            '-I', str(ROOT / 'newsnap/overlays'), '-o', str(exe)], check=True, capture_output=True)
            result = subprocess.run([str(exe)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_helpers_set_only_the_scratch_register_and_respect_the_handler_state(self):
        compiler = self.compiler()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / 'platform').mkdir()
            (p / 'cpu.h').write_text('#include <stdint.h>\ntypedef struct {uint64_t x[32],sp,pc,nzcv; __uint128_t v[32]; char rest[512];} Cpu;\n')
            (p / 'host.h').write_text('#include <stdint.h>\nuint64_t kern_now_ns(void); uint64_t frame_step_cap_ns(void);'
                                      ' void rt_log(const char *,...);\n')
            (p / 'gfx.h').write_text('#include <stdint.h>\ntypedef struct { uint64_t frames; } GfxStats;\n')
            (p / 'platform/platform.h').write_text('#include <stddef.h>\n#include <stdint.h>\nint plat_mem_read(uint64_t,void *,size_t);\n'
                                                   'int plat_mem_readable(uint64_t,uint64_t);\n')
            (p / 'fixture.c').write_text(r'''
#include <string.h>
#include "cpu.h"
#include "gfx.h"
GfxStats gfx_counters;
static uint64_t now = 1000, cap = 6944444;
int plat_mem_readable(uint64_t a, uint64_t n) { (void)a; (void)n; return 1; }
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

    def test_a_draw_only_call_places_its_clips_once_and_a_stepping_call_is_left_alone(self):
        compiler = self.compiler()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / 'platform').mkdir()
            (p / 'cpu.h').write_text('#include <stdint.h>\ntypedef struct {uint64_t x[32],sp,pc,nzcv; __uint128_t v[32]; char rest[512];} Cpu;\n')
            (p / 'host.h').write_text('#include <stdint.h>\nuint64_t kern_now_ns(void); uint64_t frame_step_cap_ns(void);'
                                      ' void rt_log(const char *,...);\n')
            (p / 'gfx.h').write_text('#include <stdint.h>\ntypedef struct { uint64_t frames; } GfxStats;\n')
            (p / 'platform/platform.h').write_text('#include <stddef.h>\n#include <stdint.h>\nint plat_mem_read(uint64_t,void *,size_t);\n'
                                                   'int plat_mem_readable(uint64_t,uint64_t);\n')
            (p / 'fixture.c').write_text(r'''
#include <string.h>
#include "cpu.h"
#include "gfx.h"
GfxStats gfx_counters;
static uint64_t now = 1000, cap = 6944444;
int plat_mem_readable(uint64_t a, uint64_t n) { (void)a; (void)n; return 1; }
uint64_t kern_now_ns(void) { return now; }
uint64_t frame_step_cap_ns(void) { return cap; }
void rt_log(const char *f, ...) { (void)f; }
int plat_mem_read(uint64_t a, void *out, size_t n) { memcpy(out, (void *)(uintptr_t)a, n); return 1; }
void snap_ui_pace_enter(Cpu *);
void snap_ui_pace_draw(Cpu *);
void snap_ui_pace_placed(Cpu *);
// One helper call of the handler call whose stack pointer is sp; -1 unless only x16 changed.
static int call(void (*fn)(Cpu *), unsigned char *object, uint64_t sp) {
    Cpu c, before;
    memset(&c, 0x5a, sizeof c);
    c.x[0] = (uint64_t)(uintptr_t)object, c.sp = sp;
    before = c;
    fn(&c);
    uint64_t x16 = c.x[16];
    c.x[16] = before.x[16];
    return memcmp(&c, &before, sizeof c) || x16 > 1 ? -1 : (int)x16;
}
int main(void) {
    unsigned char object[0x100] = {0};
    object[0xc0] = 1, object[0xc6] = 1;
    const uint64_t sp = 0x7100001000ull, other = 0x7100000800ull;
    unsigned stepped = 0, placed = 0;
    for (unsigned f = 0; f < 1440; f++, now += cap, gfx_counters.frames++) {
        int step = call(snap_ui_pace_enter, object, sp);
        if (step < 0) return 1;
        if (step) {   // a call that steps: the loop's end falls through and the drawing section draws
            stepped++;
            if (call(snap_ui_pace_placed, object, sp) != 1 || call(snap_ui_pace_draw, object, sp) != 1) return 2;
            continue;
        }
        // a call that only draws: to the loop once, back from its end, then it draws
        if (call(snap_ui_pace_draw, object, sp) != 0) return 3;
        if (call(snap_ui_pace_placed, object, other) != 1) return 4;   // another call's loop is not sent back
        if (call(snap_ui_pace_placed, object, sp) != 0) return 5;
        if (call(snap_ui_pace_draw, object, other) != 1) return 6;     // another call draws as written
        if (call(snap_ui_pace_draw, object, sp) != 1) return 7;
        if (call(snap_ui_pace_draw, object, sp) != 1 || call(snap_ui_pace_placed, object, sp) != 1) return 8;
        placed++;
    }
    if (stepped < 598 || stepped > 601 || placed != 1440 - stepped) return 9;
    // a draw-only call the handler would not carry on with runs as written: nothing to place
    for (unsigned f = 0; f < 6; f++, now += cap, gfx_counters.frames++) {
        if (call(snap_ui_pace_enter, object, sp)) continue;
        object[0xc4] = 1;
        if (call(snap_ui_pace_enter, object, sp) != 1 || call(snap_ui_pace_placed, object, sp) != 1 ||
            call(snap_ui_pace_draw, object, sp) != 1) return 10;
        object[0xc4] = 0;
        break;
    }
    // 60 fps: every call steps, no call is sent to the loop
    cap = 16666667, now += cap, gfx_counters.frames++;
    for (unsigned f = 0; f < 120; f++, now += cap, gfx_counters.frames++)
        if (call(snap_ui_pace_enter, object, sp) != 1 || call(snap_ui_pace_placed, object, sp) != 1 ||
            call(snap_ui_pace_draw, object, sp) != 1) return 11;
    return 0;
}
''')
            exe = p / 'place.exe'
            subprocess.run([compiler, str(p / 'fixture.c'), str(ROOT / 'newsnap/overlays/snap_ui_pace.c'), '-I', str(p),
                            '-I', str(ROOT / 'newsnap/overlays'), '-o', str(exe)], check=True, capture_output=True)
            result = subprocess.run([str(exe)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
