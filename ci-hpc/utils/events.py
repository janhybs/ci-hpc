#!/usr/bin/python
# author: Jan Hybs


class EnterExitEvent(object):
    def __init__(self, name):
        self.name = name
        self.on_enter = Event('%s on enter' % name)
        self.on_exit = Event('%s on exit' % name)
        self.args, self.kwargs = None, None

    def __enter__(self):
        self.on_enter(*self.args, **self.kwargs)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.on_exit(*self.args, **self.kwargs)
        return False

    def __call__(self, *args, **kwargs):
        self.args, self.kwargs = args, kwargs
        return self


class Event(list):
    """Event subscription.

    A list of callable objects. Calling an instance of this will cause a
    call to each item in the list in ascending order by index.
    # https://stackoverflow.com/a/2022629/2616048

    Example Usage:
    >>> def f(x):
    ...     print 'f(%s)' % x
    >>> def g(x):
    ...     print 'g(%s)' % x
    >>> e = Event()
    >>> e()
    >>> e.append(f)
    >>> e(123)
    f(123)
    >>> e.remove(f)
    >>> e()
    >>> e += (f, g)
    >>> e(10)
    f(10)
    g(10)
    >>> del e[0]
    >>> e(2)
    g(2)

    """

    def __init__(self, name):
        super(Event, self).__init__()
        self.name = name

    def __call__(self, *args, **kwargs):
        for f in self:
            f(*args, **kwargs)

    def __repr__(self):
        return "%s(%s)" % (self.name, list.__repr__(self))

    def on(self, handler):
        self.append(handler)

    def off(self, handler):
        self.remove(handler)
