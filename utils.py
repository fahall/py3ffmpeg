import glob
import os
from datetime import datetime, timedelta


def to_input_string(paths):
    paths = to_list_if_needed(paths)
    parts = [' '.join(['-i', f]) for f in paths]
    return ' '.join(parts)


def to_streams(paths):
    paths = to_list_if_needed(paths)
    return [num_stream(i) for i in range(len(paths))]


def to_stream_string(paths):
    paths = to_list_if_needed(paths)
    return ''.join(to_streams(paths))


def num_stream(num):
    return ''.join(['[', str(num), ']'])


def to_list_if_needed(paths):
    if isinstance(paths, str):
        paths = [paths]
    return paths


def clean_timestamp(timestamp):
    float_parts = [float(i) for i in timestamp.split(':')]
    parts = [int(i) for i in float_parts[:-1]]
    parts.append(float_parts[-1])
    padded_parts = [str(i).zfill(2) for i in parts]
    return ':'.join(padded_parts)


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


def find_video_by_name(title, root, default_extension='mkv'):
    file_pat = ''.join([title, '.*'])
    glob_pat = os.path.join(root, file_pat)
    g = glob.glob(glob_pat)
    if len(g) > 0:
        filepath = g[0]
    else:
        filepath = glob_pat.replace('*', default_extension)
    return filepath


def timestamp_wo_punctuation(timestamp):
    return ''.join(timestamp.split(':'))


def sec_to_timestamp(seconds):
    ts = timedelta(seconds=float(seconds))
    return str(ts)
