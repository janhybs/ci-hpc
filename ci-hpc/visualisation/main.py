#!/usr/bin/python
# author: Jan Hybs


from utils.dates import *
# from visualisation import *



now = now()


print(
    short_format(now)
)
print(
    human_format(now)
)
# data = load_data()

# test_name = '10_darcy'
# subdata = data[data['test-name'] == test_name]
# g = sns.FacetGrid(subdata, row="case-name", sharey=False, size=3, aspect=4)
# # g.map(plt.plot, 'duration')
# g.map(tsplot, 'git-datetime', 'duration', chart_scale=None)