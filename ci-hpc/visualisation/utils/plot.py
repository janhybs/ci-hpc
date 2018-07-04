#!/usr/bin/python
# author: Jan Hybs


import numpy as np
import pandas as pd
from matplotlib import pyplot as plt


def tsplot(x, y, reduce=np.mean, chart_scale=20, area_alpha=0.25, plot_linestyle='-', plot_marker='o', rotation=45, **kwargs):
    # assuming x and y are pandas Series
    x_label, y_label = x.name, y.name
    df = pd.DataFrame([x, y]).T

    x_axis = df.groupby(x.name, as_index=False).first()[x.name]
    grouped = df.groupby(x.name)

    means = pd.Series([y.mean() for x, y in grouped[y.name]], name=y.name)
    stds = pd.Series([y.std() for x, y in grouped[y.name]], name=y.name)
    cis = (means - stds, means + stds)

    plots = pd.Series([reduce(y) for x, y in grouped[y.name]], name=y.name)
    plt.plot(x_axis, plots, marker=plot_marker, linestyle=plot_linestyle, **kwargs)
    area_kwargs = {k:v for k,v in kwargs.items() if k not in ('label',)}
    if area_alpha > 0:
        plt.fill_between(x_axis, cis[0], cis[1], alpha=area_alpha, **area_kwargs)

    if chart_scale:
        ymean = y.mean()
        yint = (ymean / 100) * chart_scale
        plt.ylim([ymean - yint, ymean + yint])

    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.xticks(rotation=rotation)


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


