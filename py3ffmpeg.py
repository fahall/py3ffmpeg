from random import randint


class Ffmpeg():
    def get_cmd(self, in_vid, out_vid):
        flags = [self._input(in_vid), self._output(out_vid)]
        return self._get_cmd(flags)

    def _get_cmd(self, flags):
        flags.insert(0, self._begin())
        return ' '.join(flags)

    def _begin(self):
        return 'ffmpeg'

    def _input(self, in_vid=''):
        return self._flag_arg_string(self._in_flag(), [in_vid])

    def _output(self, out_vid):
        return out_vid

    def _flag_arg_string(self, flag, args):
        return ' '.join([flag, *args])

    def _in_flag(self):
        return self._flaggify('i')

    def _flaggify(self, flag):
        return ''.join(['-', flag])


class AbstractFfmpegFilter():
    def __init__(self, **kwargs):
        self.kwargs = self._valid_filter_args(kwargs)
        self.other_filter = kwargs.get('filter_to_decorate', None)
        self.flag = kwargs.get('flag', '')

    def filter(self):
        return self._filter()

    def _valid_filter_args(self, args):
        return {k: v for k, v in args.items() if self._is_passable_kwarg(k)}

    def _is_passable_kwarg(self, key):
        do_not_pass = ['strategy', 'pad_x', 'pad_y',
                       'direction', 'filter_to_decorate', 'flag']
        return key not in do_not_pass

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
        return self.other_filter.filter()


class DrawText(FfmpegFilter):
    def __init__(self, text, **kwargs):
        kwargs['flag'] = 'DrawText'
        kwargs['text'] = text
        super().__init__(**kwargs)


class Scale(FfmpegFilter):
    def __init__(self, width, height, **kwargs):
        kwargs['width'] = width
        kwargs['height'] = height
        kwargs['flag'] = 'scale'
        super().__init__(**kwargs)


class Pad(FfmpegFilter):
    def __init__(self, width, height, x=0, y=0, **kwargs):
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
    def __init__(self, in_names, **kwargs):
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
    def __init__(self, in_names, **kwargs):
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
    def __init__(self, in_names, **kwargs):
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
        if name is None:
            name = randint(0, 10000)

        name = str(name)
        if '[' not in name and ']' not in name:
            name = ''.join(['[', str(name), ']'])
        return name


class HStack(StackFilter):
    # Convenience Class
    def __init__(self, in_names, **kwargs):
        kwargs['strategy'] = PlainStacking
        kwargs['direction'] = HorizontalStackingDirection
        super().__init__(in_names, **kwargs)


class VStack(StackFilter):
    # Convenience Class
    def __init__(self, in_names, **kwargs):
        kwargs['strategy'] = PlainStacking
        kwargs['direction'] = VerticalStackingDirection
        super().__init__(in_names, **kwargs)


class ScaledVStack(StackFilter):
    def __init__(self, in_names, **kwargs):
        kwargs['strategy'] = ScaledStacking
        kwargs['direction'] = VerticalStackingDirection
        super().__init__(in_names, **kwargs)


class ScaledHStack(StackFilter):
    def __init__(self, in_names, **kwargs):
        kwargs['strategy'] = ScaledStacking
        kwargs['direction'] = HorizontalStackingDirection
        super().__init__(in_names, **kwargs)
