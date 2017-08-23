import csv
import glob
import os
import stat
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pprint import pprint

import ffmpeg_grid

ROOT = '/n/scanner/datasets/movies/private/'
TEMP = os.path.join(ROOT, 'tmp')
CONCAT_FILE = os.path.join(TEMP, 'concatenation_list')
COMMAND_FILE = os.path.join(TEMP, 'execute_concatenation')
OUT_FOLDER = '/n/scanner/alexhall/montages/'
START = 'shot_start_time'
END = 'shot_end_time'


def directory_to_montages(directory):
    csvs = glob.glob(os.path.join(directory, '*.csv'))
    files_to_run = [clip_csv_to_ffmpeg_join(c, directory) for c in csvs]
    run_montage_ffmpeg(files_to_run)


def clip_csv_to_ffmpeg_join(filename, directory):
    if not os.path.exists(TEMP):
        os.makedirs(TEMP)
    output_file = filename.replace('.csv', '.mp4')
    data = read_csv(filename)
    data = [populate_extra_data(d) for d in data]

    ffmpeg_extracts = [clip_row_to_ffmpeg_extract(d) for d in data]

    now = str(time.time())
    concat_command = get_concat_command(output_file, now)
    save_concatenate_list(data, now)
    file_to_run = save_ffmpeg_bash_script(ffmpeg_extracts,
                                          concat_command, directory, now)
    return file_to_run


def get_concat_file(now):
    return '.'.join([CONCAT_FILE, now, 'txt'])


def clip_row_to_output_path(clip_row):
    root = TEMP
    s = ''.join(clip_row[START].split(':'))
    e = ''.join(clip_row[END].split(':'))
    output_filename = ''.join([clip_row['Title'], '.', s, e, '.mpg'])
    return os.path.join(root, output_filename)


def clip_row_to_ffmpeg_extract(clip_row):
    beginning = 'ffmpeg'
    input_path = ' '.join(['-i', clip_row['input_file']])
    modifiers = ['-vf "scale=720:480:force_original_aspect_ratio=decrease,pad=720:480:(ow-iw)/2:(oh-ih)/2,setdar=16/9"',
                 '-q:a 0',
                 '-q:v 0',
                 ' -y',
                 ]
    modifiers = ' '.join(modifiers)
    input_start_flag = ' '.join(['-ss', clip_row['input_start']])
    start_time_flag = ' '.join(['-ss', clip_row['offset']])
    end_time_flag = ' '.join(['-t', clip_row['duration']])
    output_path = clip_row['output_file']
    parts = [beginning, input_start_flag, input_path,  start_time_flag, end_time_flag,  modifiers,
             output_path]
    full_command = ' '.join(parts)
    return full_command


def apply_offset(time, offset, positive=True):
    fmt = '%H:%M:%S.%f'
    s = datetime.strptime(time, fmt)
    o = datetime.strptime(offset, fmt)
    if positive:
        return (s + timedelta(o)).seconds
    else:
        return str((s - o).seconds)


def start_end_to_duration(start, end):
    fmt = '%H:%M:%S.%f'
    s = datetime.strptime(start, fmt)
    e = datetime.strptime(end, fmt)
    d = e - s
    return d.seconds


def save_concatenate_list(data, timestamp):
    parts = [d['output_file'] for d in data]
    lines = [' '.join(['file', p]) for p in parts]
    string = '\n'.join(lines)
    path = get_concat_file(timestamp)
    with open(path, 'w') as f:
        f.write(string)


def get_concat_command(output_file, timestamp):
    beginning = 'ffmpeg -f concat -safe 0 -i'
    modifiers = '-y'
    parts = [beginning, get_concat_file(timestamp), modifiers, output_file]
    string = ' '.join(parts)
    return string


def save_ffmpeg_bash_script(extracts, concat, directory, time):
    header = '#!/bin/bash'
    extract_string = '\n'.join(extracts)
    full_string = '\n'.join([header, extract_string, concat])
    cmd_file = get_command_file(directory, time)
    with open(cmd_file, 'w') as f:
        f.write(full_string)
    os.chmod(cmd_file, 0o755)
    return cmd_file


def get_command_file(directory, time):
    return '.'.join([COMMAND_FILE, time, 'sh'])


def run_montage_ffmpeg(files_to_run):
    for f in files_to_run:
        subprocess.call([f])


if __name__ == '__main__':
    directory = sys.argv[1]
    directory_to_montages(directory)
