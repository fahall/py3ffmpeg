import logging
import unittest
from sys import stderr

import py3ffmpeg

logging.basicConfig(stream=stderr)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class FfmpegWrapperTest(unittest.TestCase):

    def test_simple(self):
        i = 'input.mp4'
        o = 'out.mp4'
        cmd = py3ffmpeg.Ffmpeg().get_cmd(i, o)
        self.assertEqual(cmd, 'ffmpeg -i input.mp4 out.mp4')

    def test_draw_text(self):
        test = py3ffmpeg.DrawText('hello').filter()
        expected = "DrawText='test=hello'"

    def test_ffmpeg_filter(self):
        out = py3ffmpeg.FfmpegFilter(key='value').filter()
        self.assertEqual(out, '=key=value')

    def test_null_filter(self):
        self.assertEqual('', py3ffmpeg.NullFilter().filter())

    def test_is_passable(self):
        func = py3ffmpeg.AbstractFfmpegFilter()._is_passable_kwarg
        self.assertFalse(func('flag'))
        self.assertTrue(func('fontcolor'))
        self.assertFalse(func('filter_to_decorate'))

    def test_scale(self):
        filt = py3ffmpeg.Scale(4, 3).filter()
        self.assertEqual(filt, 'scale=width=4:height=3')

    def test_vstack(self):
        stacking = '[bob:v][eve:v]vstack=height=1080:width=1920:inputs=2'
        stacker = py3ffmpeg.VStack(
            ['[bob]', '[eve]'], height=1080, width=1920)
        actual = stacker.filter()
        self.assertIn(stacking, actual)

    def test_hstack(self):
        stacking = '[bob:v][eve:v]hstack=height=1080:width=1920:inputs=2'
        stacker = py3ffmpeg.HStack(
            ['[bob]', '[eve]'], height=1080, width=1920)
        actual = stacker.filter()
        self.assertIn(stacking, actual)

    def test_scaledvstack(self):

        bob_scale = '[bob]scale=force_original_aspect_ratio=decrease:width=1920:height=1080'
        bob_pad = 'pad=width=1920:height=1080:x=0:y=(oh-ih)/2[newbob]'
        eve_scale = '[eve]scale=force_original_aspect_ratio=decrease:width=1920:height=1080'
        eve_pad = 'pad=width=1920:height=1080:x=0:y=(oh-ih)/2[neweve]'
        stacking = '[newbob][neweve]vstack=height=1080:width=1920:inputs=2'

        # output names can be random, so do not test for equals
        stacker = py3ffmpeg.ScaledVStack(
            ['[bob]', '[eve]'], height=1080, width=1920)
        actual = stacker.filter()

        self.assertIn(bob_scale, actual)
        self.assertIn(bob_pad, actual)
        self.assertIn(eve_scale, actual)
        self.assertIn(eve_pad, actual)
        self.assertIn(stacking, actual)

    def test_decoration(self):
        pass


def run():
    unittest.main(verbosity=2)


if __name__ == '__main__':
    run()
