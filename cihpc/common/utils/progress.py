#!/bin/python3
# author: Jan Hybs
import sys
import time


basic_format = '{desc} {n:02d}/{total:02d} [{elapsed}/{remaining}] [{item_duration}/item]'
reverse_format = '{n:02d}/{total:02d} {desc} [{elapsed}/{remaining}] [{item_duration}/item]'


class Line(object):
    def __init__(self, iterable=None, total=None, format=reverse_format, file=sys.stdout, desc='', ncols=None, tty=None):
        self.iterable = iterable

        if total is None and iterable is not None:
            try:
                total = len(iterable)
            except (TypeError, AttributeError):
                total = None

        self.total = total
        self.format = format
        if tty is None:
            try:
                tty = file.isatty()
            except:
                tty = False
        self.tty = tty
        self.file = file
        self.n = 0
        self.desc = desc
        self.start_time = time.time()
        self.ncols = ncols or 80

    def start(self):
        self.start_time = time.time()
        self.update(0)

    def stop(self):
        if self.tty:
            self.file.write('\n')
            self.file.flush()

    close = stop

    @property
    def duration(self):
        if self.start_time:
            return time.time() - self.start_time
        return 0

    def update(self, n=1):
        self.n += n
        elapsed = '??:??'
        remaining = '??:??'
        item_duration = '??:??'

        if self.start_time:
            elapsed = self.format_interval(int(self.duration))

        if self.total and self.n:
            item_duration = self.format_interval(int(
                self.duration / self.n
            ))
            if self.total > self.n:
                remaining = self.format_interval(int(
                    (self.duration / self.n) * (self.total - self.n)
                ))
            else:
                remaining = '00:00'

        kwargs = dict(
            desc=self.desc,
            total=self.total,
            n=self.n,
            start_time=self.start_time,
            item_duration=item_duration,
            duration=self.duration,
            elapsed=elapsed,
            remaining=remaining,
        )

        msg = self.format.format(**kwargs)
        fmt = '{msg:<%ds}' % self.ncols
        if self.tty:
            self.file.write('\r' + fmt.format(msg=msg))
            self.file.flush()
        else:
            self.file.write(fmt.format(msg=msg) + '\n')

    @staticmethod
    def format_interval(t):
        """
        Formats a number of seconds as a clock time, [H:]MM:SS

        Parameters
        ----------
        t  : int
            Number of seconds.

        Returns
        -------
        out  : str
            [H:]MM:SS
        """
        mins, s = divmod(int(t), 60)
        h, m = divmod(mins, 60)
        if h:
            return '{0:d}:{1:02d}:{2:02d}'.format(h, m, s)
        else:
            return '{0:02d}:{1:02d}'.format(m, s)
