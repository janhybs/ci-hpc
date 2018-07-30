#!/usr/bin/python
# author: Jan Hybs
from utils import strings
from utils.logging import logger
from utils.glob import global_configuration
from utils.config import Config as cfg

cfg.init(global_configuration.cfg_path)

import warnings
warnings.filterwarnings("ignore", message="numpy.dtype size changed")
warnings.filterwarnings("ignore", message="numpy.ufunc size changed")


# import matplotlib
# matplotlib.use('Agg')
#
# import numpy as np
# import scipy as sc
# import pandas as pd
# import seaborn as sns
# import ipywidgets as w
# import utils.dateutils as dateutils
# import utils.datautils as datautils
#
#
# from matplotlib import pyplot as plt
# from artifacts.db import mongo
#
# from visualisation.jupyter.data_manipulation import ensure_iterable, normalise_vector, load_data, add_metrics, normalise_matrix
# from visualisation.jupyter.plotting import dual_plot, facetgrid_opts, plot_data, plot_mean, plot_mean_with_area, tsplot
#
#
#
# __all__ = [
#     'np', 'pd', 'sns', 'plt', 'sc', 'w', 'logger', 'mongo', 'normalise_vector', 'normalise_matrix',
#     'plot_mean', 'plot_mean_with_area', 'dual_plot', 'plot_data',
#     'dateutils', 'datautils', 'ensure_iterable',
#     'load_data', 'add_metrics', 'facetgrid_opts',
# ]


from visualisation.jupyter.data_manipulation import load_data
load_data('hello-world', use_cache=False)