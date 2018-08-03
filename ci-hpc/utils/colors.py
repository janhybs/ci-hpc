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
    return lambda x: rgb2html(rgb, '%1.2f') % x


# import argparse
# parser = argparse.ArgumentParser()
# parser.add_argument('--failed', type=str2bool, default=False)
# parser.add_argument('--uniform', type=str2bool, default=True)
# parser.add_argument('--smooth', type=str2bool, default=True)
# parser.add_argument('--separate', type=str2bool, default=True)
# parser.add_argument('--groupby', type=str, default=None)
# parser.add_argument('-f', '--filters', action='append', default=[])
#
# args = parser.parse_args('-f foo=bar, -f=bar=foobar'.split())
# args = parser.parse_args([])
# filters = dict([tuple(v.split('=')) for v in args.filters])
# print(filters)
#
# from artifacts.db.mongo import CIHPCMongo
# import pandas as pd
# import numpy as np
# from copy import deepcopy as cp
# from pluck import pluck
# from utils import strings
#
# pd.set_option('display.max_rows', 500)
# pd.set_option('display.max_columns', 500)
# pd.set_option('display.width', 1000)
#
# cihpc = CIHPCMongo.get('hello-world')
# for item in cihpc.find_all():
#     print(strings.to_json(item))
#     break
#
#
# def gets(i, o):
#     return pluck(i, o)
#
#
# def sets(i, o, v):
#     it = iter(v)
#     for x in i:
#         x[o] = next(it)
#     return i
#
#
# for item in items:
#     del item['_id']
#
#
# results = list()
#
# duration = 'duration'
# result = 'result'
#
# for item in items:
#     i = cp(item)
#     timers = i['timers']
#
#     ds = np.array(gets(timers, duration))
#     ds = ds * [0.5, 0.6, 0.7]
#
#     i['problem']['cpus'] = 2.0
#     sets(timers, duration, ds.tolist())
#     i[result][duration] = sum(ds.tolist())
#     results.append(i)
#
# for item in items:
#     i = cp(item)
#     timers = i['timers']
#
#     ds = np.array(gets(timers, duration))
#     ds = ds * [0.35, 0.5, 0.6]
#
#     i['problem']['cpus'] = 3.0
#     sets(timers, duration, ds.tolist())
#     i[result][duration] = sum(ds.tolist())
#     results.append(i)
#
#
# for item in items:
#     i = cp(item)
#     timers = i['timers']
#
#     ds = np.array(gets(timers, duration))
#     ds = ds * [0.3, 0.4, 0.5]
#
#     i['problem']['cpus'] = 4.0
#     sets(timers, duration, ds.tolist())
#     i[result][duration] = sum(ds.tolist())
#     results.append(i)
#
#
# for item in items:
#     i = cp(item)
#     timers = i['timers']
#
#     ds = np.array(gets(timers, duration))
#     ds = ds * [0.3, 0.5, 0.6]
#
#     i['problem']['cpus'] = 8.0
#     sets(timers, duration, ds.tolist())
#     i[result][duration] = sum(ds.tolist())
#     results.append(i)
#
# for item in items:
#     i = cp(item)
#     timers = i['timers']
#
#     ds = np.array(gets(timers, duration))
#     ds = ds * [0.8, 1.2, 2.6]
#
#     i['problem']['cpus'] = 16.0
#     sets(timers, duration, ds.tolist())
#     i[result][duration] = sum(ds.tolist())
#     results.append(i)
#
# with open('backup2.json', 'w') as fp:
#     fp.write(strings.to_json(items))
#
# print(len(results))
# cihpc.reports.insert_many(results)

# items = list(cihpc.aggregate(cihpc.pipeline))
# df = pd.DataFrame(items)
# df = df[["case-name", "duration", "test-name", "git-datetime"]]
# grps = df.groupby(by='git-datetime')
#
# print(grps.agg({
#     'duration': 'mean',
#     'case-name': lambda x: list(x)
# }))

# for g, d in grps:
#     print(g)
#
# with openen('backup3.json', 'w') as fp:
#     fp.write(strings.to_json(items))
#
# result = list()
# for item in items:
#     i = cp(item)
#     del i['_id']
#     i['git'] = i['libs'][0]
#     i['libs'] = []
#     result.append(i)
#
# print(cihpc.reports.delete_many({}))
# print(cihpc.reports.insert_many(result))