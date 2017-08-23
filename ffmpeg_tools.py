#from lib import decorator, extractor, finder, outputer, scaler, stacker, syncer
import subprocess

from compilation_strategies import Grid, Montage
from data import extract_data


def grid(data_file, output_file):
    strategy = Grid()
    output = compile_vids(data_file, strategy, output_file)
    return output


def montage(data_file, output_file):
    strategy = Montage()
    output = compile_vids(data_file, strategy, output_file)
    return output


def compile_vids(data_file, strategy, output_file):
    prepared_vids = prepare_for_compilation(data_file)
    compilation = strategy.run(prepared_vids)
    output = to_output(compilation, output_file)
    output = output_file
    return output


def prepare_for_compilation(data_file, scale=(1, 1), shot_duration=3):
    data = extract_vid_data(data_file)
    vids = extract_vids(data)
    #scaled_vids = scale_all(vids, scale)
    #decorated_vids = decorate_all(scaled_vids, data)
    #synced_vids = sync_all(decorated_vids, shot_duration)
    synced_vids = ['samples/temp/prep1.mp4', 'samples/temp/prep2.mp4']
    return synced_vids


def extract_vid_data(data_file, **kwargs):
    return extract_data(data_file)


def extract_vids(data,  **kwargs):
    # return finder.find(data)
    return 'dummy.mp4'


def scale_all(inputs,  **kwargs):
    # return bulk_operation(scaler.scale, inputs)
    return 'dummy.mp4'


def decorate_all(inputs, **kwargs):
    #data = kwargs.get('data', {})
    # return bulk_operation(decorator.decorate, inputs, data=data)
    return 'dummy.mp4'


def sync_all(inputs, duration_seconds):
    # return bulk_operation(syncer.sync, inputs, duration_in_seconds=duration_seconds)
    return 'dummy.mp4'


def build_grid(inputs, **kwargs):
    #row_vids = to_rows(inputs)
    #grid_vid = stack_rows(row_vids)
    # return grid_vid
    return 'dummy.mp4'


def to_rows(inputs, **kwargs):
    # return stacker.to_rows(inputs)
    return 'dummy.mp4'


def stack_rows(rows,  **kwargs):
    # return stacker.vstack(rows)
    return 'dummy.mp4'


def to_output(vid, filepath):
    cmd = ' '.join(['ffmpeg -i -f ', vid, filepath])
    subprocess.call(cmd, shell=True)
    return filepath


def bulk_operation(func, data, **kwargs):
    # return [func(d, **kwargs) for d in data]
    return 'dummy.mp4'


def directory_to_montages(directory):
    csvs = glob.glob(os.path.join(directory, '*.csv'))
    files_to_run = [clip_csv_to_ffmpeg_join(c, directory) for c in csvs]
    run_montage_ffmpeg(files_to_run)
