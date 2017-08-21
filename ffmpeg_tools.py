from lib import decorator, extractor, finder, outputer, scaler, stacker, syncer


def build_grid(data_file, output_file):
    data = extract_grid_data(data_file)
    vids = find_vids(data)
    scaled_vids = scale_all(vids)
    decorated_vids = decorate_all(scaled_vids, data)
    synced_vids = sync_all(decorated_vids)
    row_vids = to_rows(synced_vids)
    grid_vid = stack_rows(row_vids)
    output = to_output(grid_vid, output_file)
    return output


def build_montage(vids):
    return montager.montage(vids)


def extract_grid_data(data_file, **kwargs):
    return extractor.extract(data_file)


def find_vids(data,  **kwargs):
    return finder.find(data)


def scale_all(inputs,  **kwargs):
    return bulk_operation(scaler.scale, inputs)


def decorate_all(inputs, **kwargs):
    data = kwargs.get('data', {})
    return bulk_operation(decorator.decorate, inputs, data=data)


def sync_all(inputs, **kwargs):
    dur = 3
    return bulk_operation(syncer.sync, inputs, duration_in_seconds=dur)


def to_rows(inputs, **kwargs):
    return stacker.to_rows(inputs)


def stack_rows(rows,  **kwargs):
    return stacker.vstack(rows)


def to_output(vid, filepath):
    return outputer.output(vid, filepath)


def bulk_operation(func, data, **kwargs):
    return [func(d, **kwargs) for d in data]
