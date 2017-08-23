import os

from shitty_globals import ROOT


class CompilationStrategy():
    def __init__(self):

        self.make_temp_dir()

    def run(self, input_files):
        return 'compiled.mp4'

    def make_temp_dir(self):
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

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


class Grid(CompilationStrategy):
    def __init__(self):
        self.temp_dir = os.path.join(ROOT, 'tmp')
        super().__init__()
    pass


class Montage(CompilationStrategy):
    def __init__(self):
        self.CONCAT_FILE = os.path.join(TEMP, 'concatenation_list')
        self.COMMAND_FILE = os.path.join(TEMP, 'execute_concatenation')

        self.temp_dir = os.path.join(ROOT, 'tmp')
        OUT_FOLDER = '/n/scanner/alexhall/montages/'
        super().__init__()

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

    def clip_csv_to_ffmpeg_join(filename, directory):
        output_file = filename.replace('.csv', '.mp4')
        data = extract_data(filename)
        ffmpeg_extracts = [clip_row_to_ffmpeg_extract(d) for d in data]

        now = str(time.time())
        concat_command = get_concat_command(output_file, now)
        save_concatenate_list(data, now)
        file_to_run = save_ffmpeg_bash_script(ffmpeg_extracts,
                                              concat_command, directory, now)
        return file_to_run

    def get_concat_file(now):
        return '.'.join([CONCAT_FILE, now, 'txt'])
