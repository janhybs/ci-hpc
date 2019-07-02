#!/bin/python3
# author: Jan Hybs

from collections import defaultdict

import matplotlib.axes
import matplotlib.figure
from cihpc.cfg.config import global_configuration
from cihpc.common.utils.datautils import flatten
from cihpc.core.db import CIHPCMongo
import pandas as pd
import numpy as np
from scipy import stats
from matplotlib import pyplot as plt
import seaborn as sea
import itertools
from typing import Tuple, List
from sklearn.preprocessing import normalize

pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 100)
pd.set_option('display.width', 5000)
pd.set_option('precision', 3)
pd.options.display.float_format = '{:.4f}'.format
pd.set_option('max_colwidth', 200)


A_ = np.random.lognormal(mean=0.0, sigma=1.0, size=10000)
means = [0.001, .1, .5, 1.0, 2, 3, 5]
axes = plt.subplots(3, len(means), figsize=(15, 7))[1]  # type: List[List[matplotlib.axes.Axes]]

Amin = A_.min()
Amax = A_.max()

pallete = color=sea.color_palette()
for i, v in enumerate(means):
    A = (A_ - Amin) / (Amax - Amin) + v
    # A = A_ + v
    B = np.log(A)

    # C0 = (A - Amin)/(Amax - Amin)
    # C0 = (A - A.mean())/A.std()
    C = np.log(A)

    p_value_anova = stats.f_oneway(B, B+v)[1]
    print(p_value_anova)

    sea.distplot(A, bins=11, kde=False, ax=axes[0][i], color=pallete[i])
    sea.distplot(B, bins=11, kde=False, ax=axes[1][i], color=pallete[i])
    sea.distplot(C, bins=11, kde=False, ax=axes[2][i], color=pallete[i])

    axes[0][i].set_title('A + %1.2f' % v)
    axes[1][i].set_title('log(A + %1.2f)' % v)
    axes[2][i].set_title('log(|A + %1.2f|)' % v)

plt.show()
exit(0)
#
# plt.subplot(4, 1, 1)
# sea.distplot(A)
#
# plt.subplot(4, 1, 2)
# sea.distplot(np.log(A))
#
# plt.show()
# data = pd.DataFrame(dict(A=A, log=np.log(A), log10=np.log10(A), exp=np.exp(A)))
# g = sea.PairGrid(data, diag_sharey=False)
# g.map_diag(sea.distplot)
# plt.show()


class PairPlot(object):
    def __init__(self, data: pd.DataFrame, row: str, col: str, sharex=False, sharey=False, height=3, aspect=1, vars=None, prop=None):
        self.data = data
        self.row = row
        self.col = col

        self.prop = prop
        if vars:
            self.rows = vars
            self.cols = vars
        else:
            self.rows = sorted(list(self.data[row].value_counts().index))
            self.cols = sorted(list(self.data[col].value_counts().index))

        self.nrow = len(self.rows)
        self.ncol = len(self.cols)

        figsize = (self.nrow * height * aspect, self.ncol * height)
        kwargs = dict(
            figsize=figsize, squeeze=False,
            sharex=sharex, sharey=sharey
        )
        self.fig, self.axes = plt.subplots(self.nrow, self.ncol, **kwargs)

    def __iter__(self):
        return iter(itertools.permutations(self.rows, 2))

    @property
    def shape(self):
        return self.nrow, self.ncol

    def facet_axis(self, row_i=0, col_j=0):
        ax = self.axes[row_i, col_j]
        plt.sca(ax)
        return ax

    def _map(self, cond, prop):
        for i, v_i in enumerate(self.rows):
            for j, v_j in enumerate(self.cols):
                if cond(i, j):
                    A = self.data[self.data[self.row] == v_i][prop]
                    B = self.data[self.data[self.col] == v_j][prop]
                    yield i, v_i, j, v_j, A, B

    def map_diag(self, func, prop=None, **kwargs):
        for i, v_i, j, v_j, A, B in self._map(lambda i, j: i == j, prop or self.prop):
            self.facet_axis(i, j)
            func(A, **kwargs)

    def map_upper(self, func, prop=None, **kwargs):
        for i, v_i, j, v_j, A, B in self._map(lambda i, j: i < j, prop or self.prop):
            self.facet_axis(i, j)
            func(A, B, **kwargs)

    def map_lower(self, func, prop=None, **kwargs):
        for i, v_i, j, v_j, A, B in self._map(lambda i, j: i > j, prop or self.prop):
            self.facet_axis(i, j)
            func(A, B, **kwargs)

    @staticmethod
    def scatter(A, B, **kwargs):
        m = min(len(A), len(B))
        plt.scatter(A[:m], B[:m], **kwargs)

    @staticmethod
    def kdeplot(A, B, **kwargs):
        m = min(len(A), len(B))
        sea.kdeplot(A[:m], B[:m], **kwargs)

    @staticmethod
    def distplot(A, hist=True, kde=False, rug=False, **kwargs):
        kwargs['kde'] = kde
        kwargs['rug'] = rug
        kwargs['hist'] = hist
        # Test whether a sample differs from a normal distribution.
        #
        # This function tests the null hypothesis that a sample comes
        # from a normal distribution.  It is based on D'Agostino and
        # Pearson's [1]_, [2]_ test that combines skew and kurtosis to
        # produce an omnibus test of normality.
        # A = np.random.randn(10000)
        pallete = sea.color_palette()
        # A_norm = (A-A.mean())/A.std()
        A_norm = (A - A.min())/(A.max() - A.min())

        print(A_norm)
        B = np.log2(A_norm)
        k1, p1 = stats.normaltest(A)
        k2, p2 = stats.normaltest(B)

        ax = sea.distplot(A, color=pallete[0], hist_kws=dict(alpha=0.2), **kwargs)
        ax2 = ax.twiny()
        ax2 = sea.distplot(B, color=pallete[1], hist_kws=dict(alpha=0.5), ax=ax2, axlabel='log(|dur|)', **kwargs)
        plt.title('$P(N): %1.1f$%% (%1.1f%%)' % (p1*100, p2*100))


global_configuration.cfg_secret_path = '/home/jan-hybs/projects/ci-hpc/cfg/secret.yaml'
mongo = CIHPCMongo.get('flow123d')

cursor = mongo.reports.aggregate([
    {
        '$match': {
            # 'problem.stage': 'test-full',
            'problem.stage': 'test-serial',
            'git.commit': 'c0906bb4e3542132da5e4cc3368c6d50976f8058',
        }
    },
    {
        '$project': {
            '_id': 1,
            'timers': 1,
            # 'git': 1,
            # 'system': 1,
            'problem': 1,
            # 'result': 1,
        }
    },
    {
        '$unwind': '$timers',
    },
    {
        '$match': {
            'timers.name' : 'whole-program'
        }
    },
])


result = list()
for item in cursor:
    del item['_id']
    item['problem']['mesh-value'] = int(item['problem']['mesh'].split('_')[0])
    result.append(flatten(item))

# print(strings.to_yaml(result[0]))


fields = [
    'problem-case-name', 'problem-test-name',
    'problem-cpu-value', 'problem-cpu',
    'problem-mesh-value', #'problem-mesh',
    'timers-duration',
]

frame = pd.DataFrame(result)[fields]
frame = frame[frame['problem-test-name'] != '05_dfn_2d']
frame['cnt'] = 1
frame['dur'] = frame['timers-duration']
print(frame['problem-cpu-value'].value_counts())

cpu_values = list(frame['problem-cpu-value'].value_counts().index)
cpu_values_pairs = list(itertools.combinations(cpu_values, 2))
# cpu_values_pairs = [
#     # (0, 4),
#     # (0, 8)
#     # (1, 10),
#     (10, 9),
# ]

alpha = 0.05

r = list()
for g, d in frame.groupby(by=['problem-case-name', 'problem-mesh-value', 'problem-cpu']):

    gg = PairPlot(d, 'problem-cpu-value', 'problem-cpu-value', vars=[1, 2, 3], prop='dur')
    gg.map_diag(gg.distplot)
    gg.map_upper(gg.scatter)
    gg.map_lower(gg.kdeplot)
    plt.suptitle(str(g))
    plt.show()
    break

    # for cpu_a, cpu_b in cpu_values_pairs:
    #     d_a = d[d['problem-cpu-value'] == cpu_a]
    #     d_b = d[d['problem-cpu-value'] == cpu_b]
    #     a, b = d_a['dur'], d_b['dur']
    #     min_len = min(len(a), len(b))
    #
    #     if not min_len:
    #         continue
    #
    #     # Calculate the T-test for the means of two independent samples of scores.
    #     #
    #     # H_0: the samples have identical average values
    #     #
    #     # This is a two-sided test for the null hypothesis that
    #     # 2 independent samples have identical average (expected) values.
    #     # This test assumes that the populations have identical variances by default.
    #     # t_statistic, p_value = stats.ttest_ind(a, b, equal_var=False)
    #
    #     # uses Welch's t-test when heteroscedastic
    #     # Student's t-test when homoscedastic
    #     p_value_ttest = stats.ttest_ind(a, b, equal_var=False)[1]
    #
    #     # Performs a 1-way ANOVA.
    #     #
    #     # The one-way ANOVA tests the null hypothesis that two or more groups have
    #     # the same population mean. The test is applied to samples from two
    #     # or more groups, possibly with differing sizes.
    #     #
    #     # The ANOVA test has important assumptions that must be satisfied
    #     #  in order for the associated p-value to be valid.
    #     #
    #     #     1. The samples are independent.
    #     #     2. Each sample is from a normally distributed population.
    #     #     3. The population standard deviations of the groups are all equal.
    #     #        This property is known as homoscedasticity
    #     p_value_anova = stats.f_oneway(a, b)[1]
    #
    #     # Compute the Kruskal-Wallis H-test for independent samples
    #     #
    #     # The Kruskal-Wallis H-test tests the null hypothesis that the population
    #     # median of all of the groups are equal. It is a non-parametric version
    #     # of ANOVA. The test works on 2 or more independent samples, which may
    #     # have different sizes. Note that rejecting the null hypothesis does not
    #     # indicate which of the groups differs. Post-hoc comparisons between groups
    #     # are required to determine which groups are different.
    #     p_value_kruskal = stats.kruskal(a, b)[1]
    #
    #     # pick p_value
    #     p_value = p_value_ttest
    #
    #     # t, p = stats.ttest_rel(a, b)
    #
    #     # k2, p = stats.normaltest(a)
    #     # plt.hist(a)
    #     # plt.hist(b)
    #     # plt.title('%s, $p$ = %1.3f, %s' % (g, p, p <= 0.05))
    #     # plt.show()
    #     # break
    #
    #     r.append(dict(
    #         mpis=(cpu_a, cpu_b),
    #         mpi_a=cpu_a,
    #         mpi_b=cpu_b,
    #         mean_a=a.mean(),
    #         mean_b=b.mean(),
    #         group=g,
    #         p_value=p_value,
    #         p_value_perc=int(p_value*100),
    #         reject=p_value <= alpha,
    #         v_a=tuple(a.round(2)),
    #         v_b=tuple(b.round(2)),
    #         # other tests
    #         p_value_ttest=p_value_ttest,
    #         p_value_anova=p_value_anova,
    #         p_value_kruskal=p_value_kruskal,
    #     ))


def distplot(a, alpha, **kwargs):
    sea.distplot(a, **kwargs)
    # plt.xscale('log')
    plt.xlim(10e-3, 1)
    plt.axvspan(0, alpha, color='r', alpha=0.2)
    plt.axvline(alpha, color='r', linestyle='--')


pd_r = pd.DataFrame(r)
print(str(pd_r).replace(',', '\t'))
# g = sea.FacetGrid(pd_r, row='mpi_a', col='mpi_b', sharey=False)
# # g = sea.FacetGrid(pd_r, col='mpis', col_wrap=3, sharey=False)
# # g.map(sea.distplot, 'p_value', kde=False, bins=21)
# g.map(distplot, 'p_value', alpha=alpha, kde=False, bins=21)
# plt.show()




# cols = defaultdict(pd.Series)
# # cols['a'] = 5
# r = list()
# for g, d in frame.groupby(by=['problem-case-name', 'problem-mesh-value', 'problem-cpu']):
#     max_val = 0
#     for i in [1, 4, 5, 6, 7, 9]:
#         d_i = d[d['problem-cpu-value'] == i]
#         # cols.append(d_i['dur'])
#         # cols['mpi_%d' % i].name = 'mpi_%d' % i
#         vals = pd.Series(d_i['dur'][0:10])
#         # for j in range(len(vals), 20):
#         #     vals._set_values(j, np.nan)
#         cols['mpi_%d' % i] = cols['mpi_%d' % i].append(vals, ignore_index=True)
#         max_val = max(len(vals), max_val)
#     print(max_val)
#     break
# pd_t = pd.concat(cols.values(), axis=1)
# g = sea.PairGrid(pd_t)
# g.map_upper(plt.scatter)
# g.map_diag(sea.distplot)
# g.map_lower(sea.kdeplot)
# plt.show()
# print(pd_r)