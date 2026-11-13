"""Switch geography, SDL physical positions and immutable original asset."""
import hashlib
from pathlib import Path
import struct
import unittest

from newsnap.controller_art import ASSET_SHA256, BUTTON_POSITIONS, active_controls, asset_path
from newsnap import controller_art as art

ROOT = Path(__file__).resolve().parents[1]


class ControllerArtTests(unittest.TestCase):
    def test_replacement_contours_stay_inside_the_original_face_button_bounds(self):
        expected = {'X': (79, 9, 87, 17), 'Y': (71, 16, 79, 25),
                    'A': (87, 16, 94, 25), 'B': (79, 24, 87, 33)}
        self.assertEqual(art.FACE_BOUNDS, expected)
        for label, bounds in expected.items():
            x0, y0, x1, y1 = bounds
            for y, left, right in art.FACE_CONTOURS[label]:
                self.assertTrue(y0 <= y < y1 and x0 <= left < right <= x1)

    def test_face_letters_have_a_full_clear_pixel_before_the_button_outline(self):
        for label in ('A', 'B', 'X', 'Y'):
            interior = {(x, y) for y, left, right in art.FACE_MASKS[label] for x in range(left, right)}
            x0, y0 = art.FACE_GLYPH_ORIGINS[label]
            pattern = getattr(art, 'FACE_GLYPHS', art.GLYPHS)[label]
            for row, line in enumerate(pattern):
                for column, pixel in enumerate(line):
                    if pixel == '1':
                        x, y = x0+column, y0+row
                        with self.subTest(label=label, pixel=(x, y)):
                            self.assertTrue({(x, y), (x-1, y), (x+1, y), (x, y-1), (x, y+1)} <= interior)

    def test_user_original_is_copied_byte_for_byte_with_original_dimensions(self):
        data = asset_path(ROOT).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(),
                         'a8daabc38680527ad0bb4cc3115b9b07e157b0ea4f00aac27d1d042536b103c4')
        self.assertEqual(ASSET_SHA256, hashlib.sha256(data).hexdigest())
        self.assertEqual(struct.unpack('>II', data[16:24]), (104, 72))

    def test_switch_face_geography_and_physical_sdl_buttons(self):
        east, south, north, west = (BUTTON_POSITIONS[key] for key in ('A', 'B', 'X', 'Y'))
        self.assertGreater(east[0], north[0])
        self.assertGreater(south[1], east[1])
        self.assertLess(north[1], west[1])
        self.assertLess(west[0], south[0])
        for physical, expected in [('east', 'A'), ('south', 'B'), ('north', 'X'), ('west', 'Y'),
                                   ('back', '-'), ('start', '+'), ('left_stick', 'L3'),
                                   ('right_stick', 'R3'), ('left_shoulder', 'L'), ('right_shoulder', 'R')]:
            with self.subTest(physical=physical):
                self.assertEqual(active_controls({'connected': True, 'recognized': True,
                                                 'buttons': {physical: True}, 'axes': {}}), {expected})

    def test_triggers_and_dpad_show_readings_without_inventing_game_bindings(self):
        snapshot = {'connected': True, 'recognized': True,
                    'buttons': {'dpad_up': True, 'dpad_left': True, 'guide': True},
                    'axes': {'left_trigger': 32767, 'right_trigger': 0, 'leftx': 10000, 'lefty': -5000}}
        self.assertEqual(active_controls(snapshot), {'up', 'left', 'ZL'})
        self.assertNotIn('guide', active_controls(snapshot))

    def test_disconnect_or_unmapped_joystick_cannot_leave_a_stuck_highlight(self):
        snapshot = {'connected': False, 'recognized': True, 'buttons': {'east': True},
                    'axes': {'left_trigger': 32767}}
        self.assertEqual(active_controls(snapshot), set())
        snapshot.update(connected=True, recognized=False, raw_buttons=[True]*20)
        self.assertEqual(active_controls(snapshot), set())
        self.assertEqual(active_controls(None), set())

    def test_optional_mapping_has_explicit_switch_label_to_sdl_position_direction(self):
        snapshot = {'connected': True, 'recognized': True, 'buttons': {'south': True}, 'axes': {}}
        self.assertEqual(active_controls(snapshot, {'A': 'south', 'B': 'east'}), {'A'})
        self.assertEqual(active_controls(snapshot), {'B'})
