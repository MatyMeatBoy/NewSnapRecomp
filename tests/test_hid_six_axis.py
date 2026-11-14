"""GYRO-01: the six-axis IHidServer commands apply once each to the pinned donor hid service."""
from pathlib import Path
import re
import unittest

from newsnap.hid_six_axis_adapt import edits

ROOT = Path(__file__).resolve().parents[1]


class HidSixAxisAdapt(unittest.TestCase):
    def adapted(self):
        text = (ROOT / 'third_party/astral/runtime/ov_hid.c').read_text(encoding='utf-8')
        for before, after in edits()['runtime/ov_hid.c']:
            self.assertEqual(text.count(before), 1, f'seam changed: {before[:50]!r}')
            text = text.replace(before, after, 1)
        return text

    def test_every_six_axis_command_is_answered_once(self):
        text = self.adapted()
        cases = [int(n) for n in re.findall(r'case (\d+):', text)]
        self.assertEqual(len(cases), len(set(cases)), 'duplicate case label')
        for command in range(68, 84):
            if command in (66, 67):
                continue
            self.assertIn(command, cases, f'six-axis command {command} still unimplemented')

    def test_at_rest_reads_live_motion(self):
        text = self.adapted()
        self.assertIn('case 82:', text)
        self.assertIn('motion_read(motion_global(), &m, 1, kern_now_ns())', text)
        self.assertIn('#include "input.h"', text)

    def test_unknown_commands_still_fail_by_name(self):
        self.assertIn('default: ipc_unimplemented(s, rq);', self.adapted())


if __name__ == '__main__':
    unittest.main()
