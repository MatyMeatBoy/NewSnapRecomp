import unittest

from newsnap.display_scales import render_scale_choices


class DisplayScaleChoices(unittest.TestCase):
    def test_unknown_display_shows_every_step(self):
        values = list(render_scale_choices(None).values())
        self.assertEqual(values, ['50', '60', '70', '80', '90', 'game', '125', '133', '150', '175', '200', '250',
                                  '300', 'display'])

    def test_marks_the_matching_step(self):
        for height, value in ((1440, '133'), (2160, '200'), (1080, 'game')):
            marked = [v for label, v in render_scale_choices(height).items() if 'tu pantalla' in label]
            self.assertEqual(marked, [value])

    def test_drops_steps_beyond_twice_the_display_but_keeps_the_current_one(self):
        self.assertNotIn('250', render_scale_choices(1080).values())
        self.assertIn('250', render_scale_choices(1080, '250').values())
        self.assertNotIn('300', render_scale_choices(1440).values())

    def test_labels_are_unique(self):
        for height in (None, 720, 1080, 1440, 1600, 2160, 4320):
            choices = render_scale_choices(height, 'display')
            self.assertEqual(len(set(choices.values())), len(choices))


if __name__ == '__main__':
    unittest.main()
