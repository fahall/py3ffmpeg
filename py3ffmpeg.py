import re
from random import randint

import numpy as np

__USED_OUTPUT_NAMES__ = []
__CURRENT_OUTPUT_MAX__ = 2


def chunks(iterable, chunk_size):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(iterable), chunk_size):
        yield iterable[i:i + chunk_size]


class Ffmpeg():
    def __init__(self, in_vids=[], out_vid='out.mp4', vf_filters={}):
        print(in_vids)
        self.input_flag = self._input(in_vids)
        self.input_list = in_vids
        self.out_vid = out_vid
        self.flags = {'vf': self.build_vf(vf_filters)}
        assert(isinstance(out_vid, str))

    def build_vf(self, vf_filters={}):
        vf = VF(self.count)
        for f, args in vf_filters.items():
            vf.append_filter(f, **args)
        return vf

    @property
    def count(self):
        return len(self.input_list)

    def get_flag_strings(self):
        return [f.cli() for f in self.flags.values()]

    def get_cmd(self):
        i = self.input_flag
        f = self.get_flag_strings(),
        o = self.out_vid
        flags = [i]
        flags.extend(*f)
        flags.append(o)
        print(o)
        assert(isinstance(o, str))
        return self._get_cmd(flags)

    def _get_cmd(self, flags):
        flags.insert(0, self._begin())
        raw = ' '.join(flags)
        return re.sub(' +', ' ', raw)

    def _begin(self):
        return 'ffmpeg'

    def _input(self, in_vids=[]):
        inputs = [self._flag_arg_string(self._in_flag(), v) for v in in_vids]
        return ' '.join(inputs)

    def _flag_arg_string(self, flag, args):
        if isinstance(args, str):
            out = ' '.join([flag, args])
        else:
            out = ' '.join([flag, *args])
        return out

    def _in_flag(self):
        return self._flaggify('i')

    def _flaggify(self, flag):
        return ''.join(['-', flag])


class AbstractFfmpegFilter():
    def __init__(self, **kwargs):
        self.kwargs = self._valid_filter_args(kwargs)
        self.other_filter = kwargs.get('filter_to_decorate', None)
        self.flag = kwargs.get('flag', '')
        self.ignored_flags = ['strategy', 'pad_x', 'pad_y',
                              'direction', 'filter_to_decorate', 'flag',
                              'in_names']

    def __str__(self):
        return self.filter()

    def filter(self):
        return self._filter()

    def _valid_filter_args(self, args):
        return {k: v for k, v in args.items() if self._is_passable_kwarg(k)}

    def _is_passable_kwarg(self, key):
        return key not in self.ignored_flags

    def _filter(self):
        string = ''
        as_strings = [self.flag_to_text(k, v)
                      for k, v in self.kwargs.items()]
        flags = ':'.join(as_strings)
        if self.flag is not None:
            string = ''.join([self.flag, "=", flags])

        return string

    def flag_to_text(self, key, value):
        output = '='.join([str(key), str(value)])
        return output


class NullFilter(AbstractFfmpegFilter):
    def _filter(self):
        return ''


class FfmpegFilter(AbstractFfmpegFilter):
    def __init__(self, **kwargs):
        if 'filter_to_decorate' not in kwargs.keys():
            kwargs['filter_to_decorate'] = NullFilter()
        super().__init__(**kwargs)

    def filter(self):
        decoration = self._filter()
        component = self._component()
        if component:
            return ', '.join([component, decoration])
        else:
            return decoration

    def _component(self):
        return str(self.other_filter)


class DrawText(FfmpegFilter):
    def __init__(self, text='', **kwargs):
        kwargs['flag'] = 'drawtext'
        kwargs['text'] = text
        super().__init__(**kwargs)


class Scale(FfmpegFilter):
    def __init__(self, width=1920, height=1080, **kwargs):
        kwargs['width'] = width
        kwargs['height'] = height
        kwargs['flag'] = 'scale'
        super().__init__(**kwargs)


class Pad(FfmpegFilter):
    def __init__(self, width=1920, height=1080, x=0, y=0, **kwargs):
        kwargs['width'] = width
        kwargs['height'] = height
        kwargs['x'] = x
        kwargs['y'] = y
        kwargs['flag'] = 'pad'
        super().__init__(**kwargs)


class AbstractStackingDirection():
    def __init__(self, **kwargs):
        self.pad = {'x': kwargs.get('pad_x', 0),
                    'y': kwargs.get('pad_y', 0),
                    }

    def get_flag(self):
        return self.flag


class HorizontalStackingDirection(AbstractStackingDirection):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.flag = 'hstack'
        self.pad['x'] = kwargs.get('pad_x', '(ow-iw)/2')


class VerticalStackingDirection(AbstractStackingDirection):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.flag = 'vstack'
        self.pad['y'] = kwargs.get('pad_y', '(oh-ih)/2')


class AbstractStackingStrategy():
    def __init__(self, in_names=[], **kwargs):
        self.in_names = in_names

    def stack_names(self):
        parts = ''.join([n.replace(']', ':v]') for n in self.in_names])
        return parts

    def get_parts(self):
        return self.stack_names()


class PlainStacking(AbstractStackingStrategy):
    # plain old stacking
    pass


class ScaledStacking(AbstractStackingStrategy):
    # This vstack method handles scaling of inputs
    def __init__(self, in_names=[], **kwargs):
        self.store_dims(**kwargs)
        super().__init__(in_names, **kwargs)

    def store_dims(self, **kwargs):
        self.height = kwargs.get('height', -1)
        self.width = kwargs.get('width', -1)
        self.pad = kwargs.get('pad')
        self.last_row_ratio = kwargs.get('last_row_ratio', 1)

    def stack_names(self):
        stack_names = [n.replace('[', '[new') for n in self.in_names]
        return stack_names

    def _adjust_row(self, old, new):
        output = ''.join([old, self._get_adjust_cmd(), new])
        return output

    def _get_adjust_cmd(self):
        s = Scale(self.width, self.height,
                  force_original_aspect_ratio='decrease')
        adjust_cmd = Pad(self.width, self.height,
                         self.pad['x'], self.pad['y'],
                         filter_to_decorate=s)
        return adjust_cmd.filter()

    def _scale_parts(self):
        rng = range(len(self.in_names))
        old = self.in_names
        new = self.stack_names()
        scaled_parts = [self._adjust_row(old[i], new[i]) for i in rng]
        return scaled_parts

    def _scale_all(self):
        return ';'.join(self._scale_parts())

    def get_parts(self):
        start = self._scale_all()
        end = ''.join(self.stack_names())
        return ','.join([start, end])

    def _fix_last_part(self, last_row):
        '''The last row or column may not be filled if count % row_size != 0'''
        last_width = width * last_row_ratio
        old_scale = Scale(self.width, self.height).filter()
        new_scale = Scale(last_width, self.height).filter()
        return last_row.replace(old_scale, new_scale)


class StackFilter(FfmpegFilter):
    def __init__(self, in_names=[], **kwargs):
        self.in_names = in_names
        self.out_name = self._make_name(kwargs.get('name', None))
        kwargs['inputs'] = self.get_count()

        self.kwargs = kwargs
        self.direction = self._choose_direction(**kwargs)
        self.strategy = self._choose_strategy(**kwargs)
        kwargs['flag'] = self.direction.get_flag()
        super().__init__(**kwargs)

    def get_count(self):
        count = len(self.in_names)
        return count

    def store_in_names(self, in_names):
        __USED_OUTPUT_NAMES__.extend(in_names)

    def _choose_direction(self, **kwargs):
        default = HorizontalStackingDirection
        direction = kwargs.get('direction', default)
        return direction(**kwargs)

    def _choose_strategy(self, **kwargs):
        default = PlainStacking
        strategy = kwargs.get('strategy', default)
        pad = self.direction.pad
        return strategy(self.in_names, pad=pad, **kwargs)

    def get_parts(self):
        parts = self.strategy.get_parts()
        return parts

    def _filter(self):
        basic_filter = super()._filter()
        parts = [self.get_parts()]
        parts.append(basic_filter)
        parts.append(self.out_name)
        row = ''.join(parts)
        return row

    def _make_name(self, name):
        global __CURRENT_OUTPUT_MAX__
        global __USED_OUTPUT_NAMES__
        if name is None:
            name = randint(0, __CURRENT_OUTPUT_MAX__)
            while name in __USED_OUTPUT_NAMES__:
                __CURRENT_OUTPUT_MAX__ *= 2
                name = randint(0, __CURRENT_OUTPUT_MAX__)

        __USED_OUTPUT_NAMES__.append(name)

        name = str(name)
        if '[' not in name and ']' not in name:
            name = ''.join(['[', str(name), ']'])
        return name


class HStack(StackFilter):
    # Convenience Class
    def __init__(self, in_names=[], **kwargs):
        kwargs['strategy'] = PlainStacking
        kwargs['direction'] = HorizontalStackingDirection
        super().__init__(in_names, **kwargs)
        self.ignored_flags.extend(['width'])


class VStack(StackFilter):
    # Convenience Class
    def __init__(self, in_names=[], **kwargs):
        kwargs['strategy'] = PlainStacking
        kwargs['direction'] = VerticalStackingDirection
        super().__init__(in_names, **kwargs)


class ScaledVStack(StackFilter):
    def __init__(self, in_names=[], **kwargs):
        kwargs['strategy'] = ScaledStacking
        kwargs['direction'] = VerticalStackingDirection
        super().__init__(in_names, **kwargs)


class ScaledHStack(StackFilter):
    def __init__(self, in_names=[], **kwargs):
        kwargs['strategy'] = ScaledStacking
        kwargs['direction'] = HorizontalStackingDirection
        super().__init__(in_names, **kwargs)


class GridFilter(StackFilter):
    def __init__(self, in_names=[], **kwargs):
        self.height = kwargs.get('height', 1080)
        self.width = kwargs.get('width', 1920)
        self.in_names = in_names
        self.strategies = {'h': kwargs.get('h_stacker', ScaledHStack),
                           'v': kwargs.get('v_stacker', ScaledVStack), }
        self.set_size()
        self.subsets = self.build_subsets()
        super().__init__(in_names, **kwargs)

    def build_subsets(self):
        if self.size[0] > 1:
            subsets = list(chunks(self.in_names, self.size[0]))
        else:
            subsets = self.in_names
        return subsets

    def _filter(self):
        rows = self.make_rows()
        grid = self.stack_rows(rows)
        return grid.filter()

    def stack_rows(self, rows):
        row_names = [r.out_name for r in rows]
        args = {'height': self.height,
                'width': self.width,
                'filter_to_decorate': ','.join([r.filter() for r in rows])
                }
        filt = self.strategies['v'](row_names, **args)
        return filt

    def make_rows(self):
        return [self.subset_to_row(sub) for sub in self.subsets]

    def subset_to_row(self, subset):
        return self.strategies['h'](subset, width=self.width)

    def set_size(self):
        # builds a cnt x cnt grid. squares only
        count = len(self.in_names)
        rows = self.int_sqrt(count)
        self.size = (rows, rows)

    def int_sqrt(self, count):
        return int(np.ceil(np.sqrt(count)))


class VF():
    def __init__(self, count):
        self._cli = '-vf'
        self.current_filter = NullFilter()
        self.current_output_names = [
            self.num_to_input(i) for i in range(count)]
        __USED_OUTPUT_NAMES__.extend(self.current_output_names)

    def cli(self):
        cli = ''
        if not isinstance(self.current_filter, NullFilter):
            cli = ' '.join([self._cli, '"', self.current_filter.filter(), '"'])

        return cli

    def append_filter(self, vid_filter, **kwargs):
        kwargs['filter_to_decorate'] = self.current_filter
        kwargs['in_names'] = self.current_output_names
        filt = vid_filter(**kwargs)
        self._update_filter(filt)

    def _update_filter(self, filt):
        self.current_filter = filt

    def num_to_input(self, num):
        return ''.join(['[', str(num), ']'])
