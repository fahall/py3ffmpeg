def sample_to_ffmpeg_extract(sample):
    beginning = 'ffmpeg'
    input_path = ' '.join(['-i', sample['input_file']])
    modifiers = ['-vf "scale=720:480:force_original_aspect_ratio=decrease,pad=720:480:(ow-iw)/2:(oh-ih)/2,setdar=16/9"',
                 '-q:a 0',
                 '-q:v 0',
                 ' -y',
                 ]
    modifiers = ' '.join(modifiers)
    input_start_flag = ' '.join(['-ss', sample['input_start']])
    start_time_flag = ' '.join(['-ss', sample['offset']])
    end_time_flag = ' '.join(['-t', sample['duration']])
    output_path = sample['output_file']
    parts = [beginning, input_start_flag, input_path,  start_time_flag, end_time_flag,  modifiers,
             output_path]
    full_command = ' '.join(parts)
    return full_command
