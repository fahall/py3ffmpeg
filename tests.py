import logging
import subprocess
import unittest
from sys import stderr

import py3ffmpeg

logging.basicConfig(stream=stderr)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class FfmpegWrapperTest(unittest.TestCase):

    def test_simple(self):
        i = ['input.mp4']
        o = 'out.mp4'
        assert(isinstance(o, str))
        cmd = py3ffmpeg.Ffmpeg([i], o).get_cmd()
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

        # output names can be random, so do not  test for equals
        stacker = py3ffmpeg.ScaledVStack(
            ['[bob]', '[eve]'], height=1080, width=1920)
        actual = stacker.filter()

        self.assertIn(bob_scale, actual)
        self.assertIn(bob_pad, actual)
        self.assertIn(eve_scale, actual)
        self.assertIn(eve_pad, actual)
        self.assertIn(stacking, actual)

    def test_decoration(self):
        filt = py3ffmpeg.Scale(4, 3)
        scale_part = 'scale=width=4:height=3'
        self.assertEqual(filt.filter(), scale_part)
        filt = py3ffmpeg.Pad(1920, 1200, filter_to_decorate=filt)
        pad_part = 'pad=width=1920:height=1200:x=0:y=0'
        self.assertIn(scale_part, filt.filter())
        self.assertIn(pad_part, filt.filter())

    def test_grid(self):
        names = ['bob', 'eve', 'tim']
        filt = py3ffmpeg.GridFilter(names, width=2560, height=1600)
        self.assertIsInstance(filt, py3ffmpeg.GridFilter)
        self.assertEqual(len(filt.strategies), 2)

    def test_int_sqrt(self):
        filt = py3ffmpeg.GridFilter([])
        self.assertEqual(filt.int_sqrt(3), 2)
        self.assertEqual(filt.int_sqrt(9), 3)
        self.assertEqual(filt.int_sqrt(10), 4)

    def test_sizing(self):
        names = ['[bob]', '[eve]', '[tim]']
        filt = py3ffmpeg.GridFilter(names)
        self.assertEqual(filt.size, (2, 2))

    def test_subsetting(self):
        names = ['[bob]', '[eve]', '[tim]']
        filt = py3ffmpeg.GridFilter(names, width=2560, height=1600)
        self.assertIn(['[bob]', '[eve]'], filt.subsets)
        self.assertIn(['[tim]'], filt.subsets)
        self.assertEqual(len(filt.subsets), 2)

    def test_complex_get_cmd(self):
        names = ['test.mp4', 'test2.mp4', 'test3.mp4']
        filters_to_pass = {py3ffmpeg.GridFilter: {'height': 1920},
                           }
        wrap = py3ffmpeg.Ffmpeg(
            out_vid='out.mp4', in_vids=names, vf_filters=filters_to_pass)
        print(wrap.get_cmd())


def run():
    unittest.main(verbosity=2)


if __name__ == '__main__':
    run()
