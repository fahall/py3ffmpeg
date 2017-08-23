import logging
import os
import subprocess
import unittest
from pprint import pprint
from sys import stderr

import ffmpeg_tools as ffmpeg
import py3ffmpeg
import utils
from data import extract_data

logging.basicConfig(stream=stderr)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class UnitTests(unittest.TestCase):
    def setUp(self):
        self.directory = 'samples'
        self.sample_in = os.path.join(self.directory, 'data.csv')
        self.sample_vid = os.path.join(self.directory, 'test.mp4')
        self.sample_out = os.path.join(self.directory, 'output.mp4')

    def test_grid(self):
        created_grid = ffmpeg.grid(self.sample_in, self.sample_out)
        self.assertEqual(self.sample_out, created_grid)

    def test_output(self):
        ffmpeg.to_output(self.sample_vid, self.sample_out)
        self.assertTrue(os.path.exists(self.sample_out))


class StrategyTests(unittest.TestCase):
    def setUp(self):
        self.directory = 'samples'
        self.sample_in = os.path.join(self.directory, 'data.csv')
        self.sample_vid = os.path.join(self.directory, 'test.mp4')
        self.sample_out = os.path.join(self.directory, 'output.mp4')


class UtilTests(unittest.TestCase):
    def test_as_input(self):
        self.assertEqual('-i test.mp4', utils.to_input_string('test.mp4'))
        self.assertEqual('-i test.mp4 -i test2.mp4',
                         utils.to_input_string(['test.mp4', 'test2.mp4']))

    def test_as_streams(self):
        self.assertEqual(['[0]'], utils.to_streams('test.mp4'))
        self.assertEqual(['[0]', '[1]'],
                         utils.to_streams(['test.mp4', 'test2.mp4']))

        self.assertEqual('[0][1]', utils.to_stream_string(['b.mp4', 'c.mp4']))


class DataManagementTests(unittest.TestCase):
    def setUp(self):
        self.directory = 'samples'
        self.sample_in = os.path.join(self.directory, 'data.csv')
        self.sample_vid = os.path.join(self.directory, 'test.mp4')
        self.sample_out = os.path.join(self.directory, 'output.mp4')

    def test_extract_data(self):
        pprint(extract_data(self.sample_in))


def run():
    unittest.main(verbosity=2)


if __name__ == '__main__':
    run()
