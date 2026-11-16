"""MENU-FPS-01: interface motion drawn between two interface steps (newsnap/overlays/snap_ui_motion.h)."""
import os
import shutil
from pathlib import Path
import subprocess
import tempfile
import unittest

from newsnap.upstream import ROOT


class UiMotionTests(unittest.TestCase):
    def test_patch_set_has_a_settings_switch_and_only_replaces_the_matrix_handed_over(self):
        text = (ROOT / 'patches/snap-2.0.1-ui-pace.txt').read_text(encoding='utf-8')
        lines = [line.split() for line in text.splitlines() if line and not line.startswith('#')]
        self.assertIn(['set', 'snap_ui_motion', 'AC_UI_MOTION', '1'], lines)
        # the switch has a row in the settings table, so the settings file and the menus can turn it off
        from newsnap.ui_pace_adapt import edits
        self.assertIn('{"UI_MOTION", "1", "0|1", RESTART},', ''.join(new for _old, new in edits()['runtime/cfg.c']))
        # each site: the original instruction that sets x1, then the helper
        self.assertEqual([line for line in lines if line[:2] == ['site', 'snap_ui_motion']], [
            ['site', 'snap_ui_motion', 'main', '9b5c70', 'aa1503e1', 'aa1503e1', '@fn:snap_ui_motion_hand'],
            ['site', 'snap_ui_motion', 'main', '9b60fc', '91022001', '91022001', '@fn:snap_ui_motion_hand'],
            ['site', 'snap_ui_motion', 'main', '9b78f0', '91022281', '91022281', '@fn:snap_ui_motion_hand'],
        ])

    def test_motion_is_drawn_between_steps_and_jumps_and_new_or_live_clips_are_left_alone(self):
        compiler = os.environ.get('NEWSNAP_CC') or shutil.which('clang')
        if not compiler:
            self.skipTest('clang is required for native fixtures')
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)
            (p / 'fixture.c').write_text(r'''
#include <stdio.h>
#include <stdlib.h>
#include "snap_ui_motion.h"
#include "snap_ui_pace.h"

static SnapUiMotion *table;
static SnapUiPace pace = {0, 0, 0, 1};
static uint64_t frame, steps, now = 1000;
static const uint64_t period = 6944444;   // 144 fps

// One game frame: returns 1 when it steps.
static int next_frame(void) {
    now += period;
    int stepped = snap_ui_pace_decide(&pace, frame++, now, period);
    steps += (uint64_t)stepped;
    return stepped;
}
static float phase(void) { return (float)((double)pace.acc_ns / (double)SNAP_UI_PACE_STEP_NS); }
static const float *hand(uint64_t key, const float *matrix, int stepped, int live) {
    float copy[6];
    memcpy(copy, matrix, sizeof copy);
    const float *out = snap_ui_motion_matrix(table, key, matrix, frame, steps, stepped, phase(), live);
    if (memcmp(copy, matrix, sizeof copy)) exit(90);   // the player's matrix is never written
    return out;
}

int main(void) {
    table = calloc(1, sizeof *table);
    float still[6] = {1, 0, 0, 1, 100, 200}, moving[6] = {1, 0, 0, 1, 0, 50}, jumper[6] = {1, 0, 0, 1, 0, 0};
    float offstep[6] = {1, 0, 0, 1, 0, 0}, placed[6] = {1, 0, 0, 1, 0, 0};
    const uint64_t k_still = 0x1000, k_moving = 0x2000, k_jumper = 0x3000, k_offstep = 0x4000, k_placed = 0x5000;
    unsigned between = 0, frames_in_motion = 0;
    float last_x = 0;
    for (unsigned f = 0; f < 1440; f++) {
        int stepped = next_frame();
        if (stepped) moving[4] += 6, jumper[4] += 6, placed[4] += 6;       // 6 pixels a step
        if (stepped && steps % 40 == 0) jumper[4] -= 240;                  // an animation that starts over
        offstep[4] += 1;                                                   // moves on every frame
        if (hand(k_still, still, stepped, 0) != still) return 1;           // nothing that stands still is replaced
        if (hand(k_offstep, offstep, stepped, 0) != offstep) return 2;     // driven on every frame: left alone
        if (hand(k_placed, placed, stepped, 1) != placed) return 3;        // under a clip the game places: left alone
        const float *out = hand(k_moving, moving, stepped, 0);
        if (hand(k_moving, moving, stepped, 0) != out) return 4;           // the same answer within a frame
        if (steps >= 3) {
            // on the way from the step before (x - 6) to this step's x, never past it, never backwards
            if (out[4] < moving[4] - 6.001f || out[4] > moving[4] + 0.001f) return 5;
            if (out[4] < last_x - 0.001f) return 6;
            if (out[5] != 50 || out[0] != 1 || out[3] != 1) return 7;
            frames_in_motion++, between += out != moving && out[4] < moving[4];
        }
        last_x = out[4];
        const float *jump = hand(k_jumper, jumper, stepped, 0);
        // the step that starts over is handed as it is: never a position between the end and the start
        if (jump[4] < jumper[4] - 6.001f || jump[4] > jumper[4] + 0.001f) return 8;
    }
    if (frames_in_motion < 1300 || between * 10 < frames_in_motion * 8) { printf("%u of %u\n", between, frames_in_motion); return 9; }
    // a clip seen for the first time, and one back after frames in which it was not drawn, come as they are
    float fresh[6] = {1, 0, 0, 1, 500, 500};
    int stepped = next_frame();
    if (hand(0x6000, fresh, stepped, 0) != fresh) return 10;
    for (int i = 0; i < 4; i++) next_frame();   // moving is not drawn for four frames
    moving[4] += 12;
    stepped = next_frame();
    if (hand(k_moving, moving, stepped, 0) != moving) return 11;
    // the first step of a motion comes as it is; the second is drawn on the way
    float starter[6] = {1, 0, 0, 1, 0, 0};
    unsigned first = 0, later = 0, moved_steps = 0;
    for (unsigned f = 0; f < 40; f++) {
        stepped = next_frame();
        if (f >= 10 && stepped) starter[4] += 8, moved_steps++;
        const float *out = hand(0x7000, starter, stepped, 0);
        if (moved_steps == 1 && out != starter) first++;
        if (moved_steps >= 2 && out != starter) later++;
    }
    if (first || !later) return 12;
    free(table);
    return 0;
}
''')
            exe = p / 'motion.exe'
            subprocess.run([compiler, str(p / 'fixture.c'), '-I', str(ROOT / 'newsnap/overlays'), '-o', str(exe)],
                           check=True, capture_output=True)
            result = subprocess.run([str(exe)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
