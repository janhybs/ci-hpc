#!/usr/bin/python
# author: Jan Hybs

from cihpc.utils.logging import logger
from cihpc.cfg.config import global_configuration
from cihpc.cfg.cfgutil import Config as cfg


cfg.init(global_configuration.cfg_secret_path)

import warnings


warnings.filterwarnings("ignore", message="numpy.dtype size changed")
warnings.filterwarnings("ignore", message="numpy.ufunc size changed")

import matplotlib


matplotlib.use('Agg')

import numpy as np
import scipy as sc
import pandas as pd
import seaborn as sns
import ipywidgets as widgets
import cihpc.utils.dateutils as dateutils
import cihpc.utils.datautils as datautils

from matplotlib import pyplot as plt
from cihpc.artifacts.db import mongo
from cihpc.artifacts.collect.modules import unwind_report, unwind_reports

from cihpc.visualisation.jupyter.data_manipulation import normalise_vector, load_data, add_metrics, normalise_matrix
from cihpc.visualisation.jupyter.plotting import dual_plot, facetgrid_opts, plot_data, plot_mean, plot_mean_with_area


__all__ = [
    'np', 'pd', 'sns', 'plt', 'sc', 'widgets', 'logger', 'mongo', 'normalise_vector', 'normalise_matrix',
    'plot_mean', 'plot_mean_with_area', 'dual_plot', 'plot_data',
    'dateutils', 'datautils', 'unwind_report', 'unwind_reports',
    'load_data', 'add_metrics', 'facetgrid_opts',
]

#
# from cihpc.visualisation.jupyter.data_manipulation import load_data
# load_data('hello-world', use_cache=False)
