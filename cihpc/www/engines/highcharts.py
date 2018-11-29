#!/bin/python3
# author: Jan Hybs


from cihpc.common.utils import datautils as du
import numpy as np
import pandas as pd


class AChart(object):
    _metrics = list()
    _chart_type = None
    _chart_name = None

    def __init__(self, opts, enabled=False):
        self.opts = opts
        self.enabled = enabled

        self.chart_type = self._chart_type
        self.chart_name = self._chart_name
        self.metrics = self._metrics

    def get_metrics(self):
        if self.enabled:
            return {k: True for k in self.metrics}
        return {}

    @staticmethod
    def __round_and_fill(df):
        if isinstance(df, pd.DataFrame):
            return du.fillna(df.round(2))
        elif isinstance(df, np.ndarray):
            try:
                return np.nan_to_num(np.around(df, 2), None)
            except Exception as e:
                return df
        return df

    def get_chart_data(self, df):
        return self.__round_and_fill(
            self._compute(df)
        )

    def get_chart(self, df, title=None, **kwargs):
        result = dict(
            type=self.chart_type,
            data=self.get_chart_data(df),
            name=self.chart_name + (' (%s)' % title if title not in ('*', '', None) else ''),
        )
        result.update(kwargs)
        return result

    def _compute(self, df):
        raise Exception("Not supported")

    def __bool__(self):
        return self.enabled


class ChartErrorBar(AChart):
    _metrics = ['mean', 'median']
    _chart_type = 'errorbar'
    _chart_name = '{} +- {:1.1f}%'

    def __init__(self, opts, enabled=False, interval=0.025, metric='mean'):
        super(ChartErrorBar, self).__init__(opts, enabled)
        self.interval = interval
        self.metric = metric
        self.chart_name = self._chart_name.format(metric, (interval * 100))

    def _compute(self, df):
        result = pd.DataFrame()
        result['x'] = list(df.index)
        result['low'] = list(df[self.opts.y][self.metric] * (1 + self.interval / 2))
        result['high'] = list(df[self.opts.y][self.metric] * (1 - self.interval / 2))
        return result


class ChartErrorColumn(AChart):
    _metrics = ['mean', 'median']
    _chart_type = 'columnrange'
    _chart_name = '{} +- {:1.1f}%'

    def __init__(self, opts, enabled=False, interval=0.025, metric='mean'):
        super(ChartErrorColumn, self).__init__(opts, enabled)
        self.interval = interval
        self.metric = metric
        self.chart_name = self._chart_name.format(metric, (interval * 100))

    def _compute(self, df):
        result = pd.DataFrame()
        result['x'] = list(df.index)
        result['low'] = list(df[self.opts.y][self.metric] * (1 + self.interval / 2))
        result['high'] = list(df[self.opts.y][self.metric] * (1 - self.interval / 2))
        return result


class ChartCI(AChart):
    _metrics = ['mean', 'ci']
    _chart_type = 'areasplinerange'
    _chart_name = '95% CI'

    def _compute(self, df):
        result = pd.DataFrame()
        result['x'] = list(df.index)
        result['low'] = list(df[self.opts.y]['mean'] - df[self.opts.y]['ci'])
        result['high'] = list(df[self.opts.y]['mean'] + df[self.opts.y]['ci'])
        return result


class ChartSTD(AChart):
    _metrics = ['mean', 'std']
    _chart_type = 'areasplinerange'
    _chart_name = 'mean +- std'

    def _compute(self, df):
        result = pd.DataFrame()
        result['x'] = list(df.index)
        result['low'] = list(df[self.opts.y]['mean'] - df[self.opts.y]['std'])
        result['high'] = list(df[self.opts.y]['mean'] + df[self.opts.y]['std'])
        return result


class ChartBoxPlot(AChart):
    _metrics = ['min', '25%', '50%', '75%', 'max']
    _chart_type = 'boxplot'
    _chart_name = 'boxplot'

    def _compute(self, df):
        result = df[self.opts.y].reset_index()[
            [self.opts.x, 'min', '25%', '50%', '75%', 'max']
        ]
        return result


class ChartMean(AChart):
    _metrics = ['mean']
    _chart_type = 'line'
    _chart_name = 'mean'

    def _compute(self, df):
        result = pd.DataFrame()
        result['x'] = list(df.index)
        result['y'] = list(df[self.opts.y]['mean'])
        return result


class ChartMedian(AChart):
    _metrics = ['median']
    _chart_type = 'line'
    _chart_name = 'median'

    def _compute(self, df):
        result = pd.DataFrame()
        result['x'] = list(df.index)
        result['y'] = list(df[self.opts.y]['median'])
        return result


class ChartGroup(object):
    y_metrics_default = {
        'mean'  : np.mean,
        'median': np.median,
        'min'   : np.min,
        'max'   : np.max,
        'std'   : np.std,
        '25%'   : lambda x: np.percentile(x, 25),
        '50%'   : np.median,
        '75%'   : lambda x: np.percentile(x, 75),
        'ci'    : du.mean_confidence_interval,
    }

    def __init__(self, chart_options, options):
        self.mean_chart = ChartMean(chart_options, options.get('show-mean', True))
        self.median_chart = ChartMedian(chart_options, options.get('show-median', False))
        metric = 'median' if self.median_chart else 'mean'

        self.boxplot_chart = ChartBoxPlot(chart_options, options.get('show-boxplot', False))
        self.ci_chart = ChartCI(chart_options, options.get('show-ci', False))
        self.std_chart = ChartSTD(chart_options, options.get('show-stdbar', False))
        self.errorbar_chart = ChartErrorBar(chart_options, options.get('show-errorbar', False), metric=metric)

        self.all_charts = [
            self.mean_chart, self.median_chart, self.boxplot_chart, self.ci_chart,
            self.std_chart, self.errorbar_chart
        ]

        allowed = set([k for ch in self.all_charts for k in ch.get_metrics().keys()])
        self.y_metrics = {k: v for k, v in self.y_metrics_default.items() if k in allowed}

    def __bool__(self):
        for g in self.all_charts:
            if g:
                return True
        return False
