import csv
import os

from shitty_globals import ROOT
from utils import (apply_offset, clean_timestamp, find_video_by_name,
                   sec_to_timestamp, start_end_to_duration,
                   timestamp_wo_punctuation)

START = 'shot_start_time'
END = 'shot_end_time'
TEMP = os.path.join(ROOT, 'temp')


def extract_ngrams(filename):
    data = read_csv(filename)
    data = [populate_extra_data(d) for d in data]
    return data


def read_csv(filename):
    with open(filename, 'r') as f:
        data = csv.DictReader(f)
        entries = [row for row in data]
    return entries


def populate_extra_data(sample):
    sample = find_outer_bounds(sample)
    sample = clean_times(sample)
    sample = get_input_output_files(sample)
    return sample


def find_outer_bounds(sample):
    ngram_bnd = 'internal_boundaries_as_seconds'
    if ngram_bnd in sample.keys():
        bounds = sample[ngram_bnd].split(',')
        sample[START] = sec_to_timestamp(bounds[0])
        sample[END] = sec_to_timestamp(bounds[-1])
    return sample


def clean_times(sample):
    sample = clean_clip_times(sample)
    sample = append_duration(sample)
    sample = offset_input_for_hq_speedup(sample)
    return sample


def clean_clip_times(sample):
    start = clean_timestamp(sample[START])
    end = clean_timestamp(sample[END])
    sample[START] = start
    sample[END] = end
    return sample


def append_duration(sample):
    sample['duration'] = str(start_end_to_duration(sample[START], sample[END]))
    return sample


def offset_input_for_hq_speedup(sample):
    '''ffmpeg is faster if the input is trimmed instead of the output.
    Sometimes, keyframes are not sampled when trimming the input.
    grab an extra 2 minutes prior to ensure we get a keyframe.
    '''

    offset = '00:02:00.000'
    sample['offset'] = offset
    sample['input_start'] = apply_offset(sample[START], offset, positive=False)
    return sample


def get_input_output_files(sample):
    sample['input_file'] = sample_to_input_path(sample)
    sample['output_file'] = sample_to_output_path(sample)
    return sample


def sample_to_input_path(sample):
    root = ROOT
    title = sample_to_title(sample)
    filepath = find_video_by_name(title, root)
    return filepath


def sample_to_title(sample):
    return sample['Title']


def sample_to_output_path(sample):
    root = TEMP
    s = timestamp_wo_punctuation(sample[START])
    e = timestamp_wo_punctuation(sample[END])
    output_filename = ''.join([sample['Title'], '.', s, e, '.mpg'])
    return os.path.join(root, output_filename)
