#!/bin/python3
# author: Jan Hybs


import colorama
import time
import tqdm
import sys
colorama.init()


class Cout(object):
    _fields = dict(
        bright=colorama.Style.BRIGHT,
        bold=colorama.Style.BRIGHT,

        normal=colorama.Style.NORMAL,
        dim=colorama.Style.DIM,

        reset=colorama.Style.RESET_ALL,
        clear=colorama.Style.RESET_ALL,

        invert='\033[7m',
        inverted='\033[7m',

        red=colorama.Fore.RED,
        green=colorama.Fore.GREEN,
        blue=colorama.Fore.BLUE,

        yellow=colorama.Fore.YELLOW,
        cyan=colorama.Fore.CYAN,
        magenta=colorama.Fore.MAGENTA,
        white=colorama.Fore.WHITE,
        black=colorama.Fore.BLACK,

        on_red=colorama.Back.RED,
        on_green=colorama.Back.GREEN,
        on_blue=colorama.Back.BLUE,

        on_yellow=colorama.Back.YELLOW,
        on_cyan=colorama.Back.CYAN,
        on_magenta=colorama.Back.MAGENTA,
        on_white=colorama.Back.WHITE,
        on_black=colorama.Back.BLACK,

    )

    def __init__(self, file):
        self.file = file or sys.stderr

    @classmethod
    def get(cls, string, *styles, reset=True):
        message = ''.join([cls._fields.get(x.lower()) for x in styles]) + str(string)
        if reset:
            return message + cls._fields.get('reset')
        else:
            return message

    write = print


class CoutInvert(Cout):
    def print(self, message, *styles, percent=0.0):
        self.file.write(self.get(message, *styles, percent=percent))

    @classmethod
    def get(cls, message, *styles, percent=0.0):
        msg = str(message)

        if isinstance(percent, float):
            percent = int(len(msg) * percent)

        left = msg[:percent]
        right = msg[percent:]
        result = ''
        if left:
            result += super(CoutInvert, cls).get(left, *styles, 'invert', reset=True)
        if right:
            result += super(CoutInvert, cls).get(right, *styles, reset=True)
        return result

    write = print


class Ctqdm(tqdm.tqdm):

    def __init__(self, iterable=None, desc=None, total=None, leave=True, file=None, ncols=None, mininterval=0.1,
                 maxinterval=10.0, miniters=None, ascii=None, disable=False, unit='it', unit_scale=False,
                 dynamic_ncols=False, smoothing=0.3, bar_format=None, initial=0, position=None, postfix=None,
                 unit_divisor=1000, gui=False, **kwargs):
        try:
            import shutil
            size = shutil.get_terminal_size((80, 20))
            columns = size.columns
        except:
            columns = 80

        if not columns or isinstance(columns, int):
            columns = 80

        super().__init__(iterable, desc, total, leave, file, columns, mininterval, maxinterval, miniters, ascii, disable,
                         unit, unit_scale, dynamic_ncols, smoothing, bar_format, initial, position, postfix,
                         unit_divisor, gui, **kwargs)

    def __repr__(self, elapsed=None):
        prc = self.n / self.total
        fmt = self.format_meter(
            self.n, self.total,
            elapsed if elapsed is not None else self._time() - self.start_t,
            self.dynamic_ncols(self.fp) if self.dynamic_ncols else self.ncols,
            self.desc, self.ascii, self.unit,
            self.unit_scale, 1 / self.avg_time if self.avg_time else None,
            self.bar_format, self.postfix, self.unit_divisor)

        if self.ncols:
            fmt = ('{:.<%ss}' % self.ncols).format(fmt)

        if prc == 1.0:
            return fmt
        return CoutInvert.get(fmt, percent=prc)
