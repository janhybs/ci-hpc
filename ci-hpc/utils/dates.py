#!/usr/bin/python
# author: Jan Hybs

import datetime as dt
import time as t
import maya


epoch = dt.datetime(1970, 1, 1)


def to_seconds(datetime):
    return (datetime - epoch).total_seconds()


to_minutes = lambda x: to_seconds(x) / 60
to_hours   = lambda x: to_seconds(x) / (60 * 60)
to_days    = lambda x: to_seconds(x) / (60 * 60 * 24)


def now():
    return maya.now()


def short_format(datetime):
    if type(datetime) is maya.MayaDT:
        return short_format(datetime.datetime())
    return datetime.strftime('%Y/%m/%d')


def human_format(datetime):
    if type(datetime) is maya.MayaDT:
        return human_format(datetime.datetime())
    return maya.MayaDT.from_datetime(datetime).slang_time()