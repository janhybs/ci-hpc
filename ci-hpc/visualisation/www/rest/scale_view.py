#!/bin/python3
# author: Jan Hybs

import argparse

import itertools

import time
from flask_restful import Resource
from artifacts.db.mongo import CIHPCMongo

import pandas as pd
import seaborn as sns

from utils import strings
from utils.datautils import ensure_iterable
from utils.html_argparse import HTMLArgparse
from utils.logging import logger
from utils.timer import Timer
from visualisation.www.plot.cfg.project_config import ProjectConfig
from visualisation.www.plot.highcharts import highcharts_sparkline_in_time


def str2bool(v):
    if v.lower() in ('yes', 'true', '1'):
        return True
    elif v.lower() in ('no', 'false', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


parser = HTMLArgparse()
parser.add_argument('-f', '--ff', action=HTMLArgparse.ACTION_DICT, default={}, dest='filters')
parser.add_argument('-g', '--gg', action=HTMLArgparse.ACTION_DICT, default={}, dest='groups')


class ScaleView(Resource):

    @Timer.decorate('Scale: get', logger.info)
    def get(self, project, options=''):
        if options:
            options = ('--' + options.rstrip(',').replace(',', ' --')).split()
        else:
            options = []

        print(options)

        config = ProjectConfig.get(project)
        args = parser.parse_args(options)

        filters = {}
        for k in args.filters:
            if k.startswith('.'):
                if k[1:] in config.test_view.groupby:
                    filters[config.test_view.groupby.get(k[1:])] = args.filters[k]
            elif k.startswith('filter'):
                filters[k[7:]] = args.filters[k]

        with Timer('config init', log=logger.debug):
            mongo = CIHPCMongo.get(project)
            filters = config.test_view.get_filters(filters)
            projection = config.test_view.get_projection()

        return [1,2,3]