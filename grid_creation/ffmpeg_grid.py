import csv
import logging
import os
import subprocess
from math import ceil, sqrt
from pprint import pprint

import cv2
import numpy as np

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def get_video_dimensions(vid_path):
    vcap = cv2.VideoCapture(vid_path)  # 0=camera
    output = {}
    if vcap.isOpened():
        # get vcap property
        output['width'] = vcap.get(cv2.CAP_PROP_FRAME_WIDTH)   # float
        output['height'] = vcap.get(cv2.CAP_PROP_FRAME_HEIGHT)  # float
        output['fps'] = vcap.get(cv2.CAP_PROP_FPS)
    else:
        warn = ' '.join([vid_path, "not found."])
        logger.warning(warn)
    return output


def save_img(filepath, img):
    cv2.imwrite(filepath, img)


def get_grid_size(list_of_clips):
    full_length = len(list_of_clips)
    dim = ceil(sqrt(full_length))
    width = dim
    height = ceil(full_length / dim)
    return height, width


def ffmpeg_drawtext(text, **kwargs):
    kwargs['font_size'] = kwargs.get(font_size, 40)
    kwargs['font_color'] = kwargs.get(font_color, 'yellow')
    kwargs['borderw'] = kwargs.get(border_width, 3)
    string = ffmpeg_filter('drawtext', kwargs)
    return string


def ffmpeg_filter(filter_name, flags):
    flags_as_strings = [flag_to_text(k, v) for k, v in flags.items()]
    flags = ':'.join(flags_as_string)
    string = ''.join([filter_name, "='", flags, "'"])
    return string


def flag_to_text(key, value):
    return '='.join([key, value])


def ffmpeg_grid_cmd(list_of_clips, output_file='grid.mp4', pix_height=1080, pix_width=1920):
    count = len(list_of_clips)
    h, w = get_grid_size(list_of_clips)
    row_height = pix_height // h
    row_width = pix_width
    col_width = pix_width // w
    print(':'.join([str(v) for v in [row_height, row_width, col_width]]))
    beginning = 'ffmpeg'
    individual_inputs = [' '.join(['-i', clip]) for clip in list_of_clips]
    inputs = ' '.join(individual_inputs)
    filt = grid_filter(h, w, count, row_height, row_width)
    filt = ''.join(['-filter_complex "', filt, '"'])
    output = ''.join(['-map "[video]" ', ' -y ', output_file])
    full_cmd = ' '.join([beginning, inputs, filt, output])
    return full_cmd


def grid_filter(height, width, entries, pix_height, pix_width):
    names = list('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
    names = [''.join(['[', n, ']']) for n in names]
    rows = []
    row_names = []
    lens = []
    for row_idx in range(height):
        start = row_idx * width
        end = min(start + width, entries)
        count = end - start
        if end > start:
            n = names[row_idx]
            lens.append(count)
            cmd = grid_row(start, end, n)
            rows.append(cmd)
            row_names.append(n)
    last_row_ratio = lens[-1] / lens[0]
    vstack_cmd = get_vstack_cmd(
        row_names, pix_height, pix_width, last_row_ratio)
    rows.append(vstack_cmd)
    return ';'.join(rows)


def get_vstack_cmd(row_names, height, width, last_row_ratio):
    dim_str = ':'.join([str(width), str(height)])
    last_width = width * last_row_ratio
    last_row_dim_str = ':'.join([str(last_width), str(height)])
    print(dim_str)
    new_row_names = [n.replace('[', '[new') for n in row_names]
    scale_command = ''.join(['scale=', dim_str,
                             ':force_original_aspect_ratio=decrease',
                             ',pad=', dim_str, ':0:(oh-ih)/2'
                             ])

    rng = range(len(row_names))
    individual_scales = [''.join([row_names[idx],
                                  scale_command,
                                  new_row_names[idx]]) for idx in rng]

    old_scale = ''.join(['scale=', dim_str])
    new_scale = ''.join(['scale=', last_row_dim_str])

    individual_scales[-1] = individual_scales[-1].replace(old_scale, new_scale)
    full_scale = ';'.join(individual_scales)
    count = str(len(row_names))
    cmd = ''.join(new_row_names)
    cmd = ''.join([cmd, 'vstack=inputs=', count, '[video]'])
    cmd = ';'.join([full_scale, cmd])
    return cmd


def grid_row(start, stop, name):
    parts = [''.join(['[', str(i), ':v]'])for i in range(start, stop)]
    parts.append('hstack=inputs=')
    parts.append(str(stop - start))
    parts.append(name)
    row = ''.join(parts)
    return row


def create_grid(list_of_clips):
    command = ffmpeg_grid_cmd(list_of_clips)
    print(command)
    subprocess.run(command, shell=True)
