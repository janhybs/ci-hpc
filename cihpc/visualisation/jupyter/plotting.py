#!/bin/python3
# author: Jan Hybs
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

from cihpc.utils import datautils as datautils
from cihpc.utils.datautils import ensure_iterable
from cihpc.visualisation.plotting import tsplot


def dual_plot(conditions, *args, plot_func, error_kwargs, **kwargs):
    ok_args = [a[conditions == 0] for a in args]
    er_args = [a[conditions == 1] for a in args]
    plot_func(*ok_args, **kwargs)
    for k, v in error_kwargs.items():
        kwargs[k] = v
    plot_func(*er_args, **kwargs)


def plot_data(
        data, x='commit-date', y='duration',
        filters=None, type='line',
        groups=['case-name', 'test-size'],
        hue=None,
        sharex=False, sharey=None):
    """
    :type filters: dict
    :type groups: list[str]
    """
    groups = ensure_iterable(groups)
    subdata = datautils.filter_rows(data, **filters) if filters else data
    opts = dict(
        aspect=2,
        size=3,
        sharex=sharex if sharex is not None else False,
        sharey=sharey if sharey is not None else (y.find('relative') != -1)
    )
    if len(groups) == 2:
        a_count, b_count = [len(subdata.groupby(g).groups) for g in groups]
        if a_count > b_count:
            groups = groups[::-1]
            a_count, b_count = b_count, a_count
        if a_count == 1:
            opts.update(dict(col=groups[1], col_wrap=2))
            opts['hue'] = groups[1] if hue is None else hue
        else:
            opts.update(dict(zip(['col', 'row'], groups)))
            opts['hue'] = groups[1] if hue is None else hue
    else:
        opts.update(dict(col=groups[0], col_wrap=2))
        opts['hue'] = groups[0] if hue is None else hue

    if type == 'line':
        g = sns.FacetGrid(subdata, **opts)
        g.map(plot_mean_with_area, x, y)
        g.map(tsplot, x, y, chart_scale=None, reduce=np.median)

        g.map(plt.scatter, x, y, alpha=0.3, marker='x')
        # ok_args = dict(alpha=0.3, marker='x', plot_func=plt.scatter)
        # error_kwargs = dict(marker='D', color='r', alpha=1)
        # g.map(dual_plot, 'returncode', x, y, **ok_args, error_kwargs=error_kwargs)

    elif type == 'hist':
        opts.update(dict(aspect=4, size=1.5), hue='case-name' if hue is None else hue)
        g = sns.FacetGrid(subdata, **opts)
        g.map(plt.hist, y)

    return subdata


def facetgrid_opts(data, x, y, z, x_space=15, aspect=2, sharex=False, sharey=False):
    # g = sns.FacetGrid(subdata, row='case-name', sharey=False, sharex=sharex, size=3, aspect=2, hue='case-name')
    # g = sns.FacetGrid(subdata, col='case-name', col_wrap=2, sharey=False, sharex=sharex, size=3, aspect=2, hue='case-name')

    x_series, y_series = data[x], data[y]
    col_wrap = 1 + int(np.floor(x_space / len(datautils.olist(x_series))))
    col_wrap = min(3, col_wrap)
    inches = 8

    if col_wrap == 1:
        return dict(
            row=y_series.name,
            size=inches / aspect,
            aspect=aspect,
            hue=y_series.name,
            sharey=sharey or False,
            sharex=sharex or (True if z.find('relative') != -1 else False)
        )
    else:
        return dict(
            col=y_series.name,
            col_wrap=col_wrap,
            aspect=aspect,
            size=int((inches - col_wrap + 0.0) / aspect),
            hue=y_series.name,
            sharey=sharey or False,
            sharex=sharex or (True if z.find('relative') != -1 else False)
        )


def plot_mean(y, **kwargs):
    plt.axhline(y=np.mean(y), ls=":", **kwargs)


def plot_mean_with_area(x, y, data=None, estimator=np.mean, percentiles=((-2.5, +2.5), (-5.0, +5.0)), **kwargs):
    if not data:
        data = pd.DataFrame([x, y]).T

    first_x = sorted(list(set(data[x.name])))[0]
    estimate = estimator(data[data[x.name] == first_x][y.name])
    estimate_p = estimate / 100.0

    for pl, pu in percentiles:
        lower_estimate = estimate + estimate_p * pl
        upper_estimate = estimate + estimate_p * pu
        plt.fill_between(data[x.name], lower_estimate, upper_estimate, alpha=0.1, **kwargs)
