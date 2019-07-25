#!/bin/python3
# author: Jan Hybs

import argparse
import pathlib
import maya
from cihpc.common.utils.vcs import HistoryBrowser


default_min_age = maya.when('6 months ago')


parser = argparse.ArgumentParser()
parser.add_argument('-u', '--url', help='URL of the repo', default='https://github.com/flow123d/flow123d.git')
parser.add_argument('-b', '--branch', help='Specify branch', default=None)
parser.add_argument('--min-age', help='Drop all commit older than this date', type=maya.when, default=default_min_age)

parser.add_argument('-n', '--limit', help='Number od commits to process', type=int, default=10)
parser.add_argument('repo', help='Path to the repo', type=pathlib.Path, default=pathlib.Path('.'))


args = parser.parse_args()
repo: pathlib.Path = args.repo
url: str = args.url
limit: int = args.limit
branch: str = args.branch
min_age: maya.MayaDT = args.min_age


history_browser = HistoryBrowser(url, repo)
history_browser.commit_surroundings('68afef4')
# for hist in history_browser.git_history(None, limit=limit, min_age=min_age):
#     print(hist)
