#!/bin/python3
# author: Jan Hybs
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt


def tsplot(x, y, reduce=np.mean, chart_scale=20, area_alpha=0.25, plot_linestyle='-', plot_marker='o', rotation=45,
           **kwargs):
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
    area_kwargs = {k: v for k, v in kwargs.items() if k not in ('label',)}
    if area_alpha > 0:
        plt.fill_between(x_axis, cis[0], cis[1], alpha=area_alpha, **area_kwargs)

    if chart_scale:
        ymean = y.mean()
        yint = (ymean / 100) * chart_scale
        plt.ylim([ymean - yint, ymean + yint])

    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.xticks(rotation=rotation)
