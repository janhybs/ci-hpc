#!/bin/python3
# author: Jan Hybs


def hex2rgb(hex):
    """
    method will convert given hex color (#00AAFF)
    to a rgb tuple (R, G, B)
    """
    h = hex.strip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb2hex(rgb):
    """
    method will convert given rgb tuple (or list) to a
    hex format (such as #00AAFF)
    """
    return '#%02x%02x%02x' % rgb


def rgb2html(rgb, alpha=None):
    """
    method will convert given rgb tuple to html representation
    rgb(R, G, B)
    if alpha is set, it will be included
    rgb(R, G, B, )
    """
    if alpha is not None:
        return 'rgba({0:d}, {1:d}, {2:d}, {3:s})'.format(
            *rgb,
            alpha if isinstance(alpha, str) else '%1.2f' % float(alpha)
        )
    return 'rgb({0:d}, {1:d}, {2:d})'.format(*rgb)


def configurable_html_color(rgb):
    """
    method will return function which take a single argument (float number)
    and returns a html rgba(R, G, B, A) representation of the color, where A is
    the argument given to function returned.
    """
    return lambda x: rgb2html(rgb, x)

