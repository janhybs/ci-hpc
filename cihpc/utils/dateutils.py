#!/usr/bin/python
# author: Jan Hybs

import datetime as dt


epoch = dt.datetime(1970, 1, 1)


def to_seconds(datetime):
    return (datetime - epoch).total_seconds()


to_minutes = lambda x: to_seconds(x) / 60
to_hours = lambda x: to_seconds(x) / (60 * 60)
to_days = lambda x: to_seconds(x) / (60 * 60 * 24)


def now():
    import maya

    return maya.now()


def short_format(datetime):
    import maya

    if type(datetime) is maya.MayaDT:
        return short_format(datetime.datetime())
    return datetime.strftime('%Y/%m/%d')


def long_format(datetime):
    import maya

    if type(datetime) is maya.MayaDT:
        return short_format(datetime.datetime())
    return datetime.strftime('%Y/%m/%d-%H:%M:%S')


def human_format(datetime):
    import maya

    if type(datetime) is maya.MayaDT:
        return human_format(datetime.datetime())
    return maya.MayaDT.from_datetime(datetime).slang_time()


def human_format2(datetime):
    import maya

    if type(datetime) is maya.MayaDT:
        return human_format2(datetime.datetime())
    return maya.MayaDT.from_datetime(datetime).slang_date()


def human_interval(start, end=dt.datetime.now()):
    import maya

    td = maya.MayaInterval(maya.MayaDT.from_datetime(start), maya.MayaDT.from_datetime(end)).timedelta
    days, hours, minutes = td.days, td.seconds // 3600, (td.seconds // 60) % 60
    if not days:
        if not hours:
            return '%d minute%s' % (minutes, 's' if minutes > 1 else '')
        return '%d hour%s' % (hours, 's' if hours > 1 else '')
    return '%d day%s' % (days, 's' if days > 1 else '')
