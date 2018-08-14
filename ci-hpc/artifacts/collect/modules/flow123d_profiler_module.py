#!/usr/bin/python
# author: Jan Hybs


import json
import os
import re

from artifacts.collect.modules import CollectResult, AbstractCollectModule, CIHPCReport


class CollectModule(AbstractCollectModule):

    _floats = [
        re.compile('cumul-time-.+'),
        re.compile('percent'),
        re.compile('timer-resolution'),
    ]

    _ints = [
        re.compile('call-count-.+'),
        re.compile('memory-.+'),
        re.compile('file-line'),
        re.compile('task-size'),
        re.compile('run-process-count'),
    ]

    _dates = [
        re.compile('run-started-at'),
        re.compile('run-finished-at'),
    ]

    _children = 'children'

    def process(self, object, from_file=None):
        # initial report
        report = CIHPCReport()

        # if status file is present, enrich the report
        if from_file and os.path.exists(from_file):
            dir_name = os.path.dirname(from_file)
            status_file = os.path.join(dir_name, 'runtest.status.json')
            if os.path.exists(status_file):
                with open(status_file, 'r') as fp:
                    status_json = json.loads(fp.read())

                props = ['returncode', 'duration']
                for p in props:
                    if p in status_json:
                        report.result[p] = status_json[p]

                props = ['test-name', 'case-name']
                for p in props:
                    if p in status_json:
                        report.problem[p] = status_json[p]

        # grab version while we're at it
        report.git['version'] = object['program-version']
        # grab task size as well
        report.problem['task-size'] = int(object['task-size'])

        # get cpu
        cpus = float(object['run-process-count'])
        report.problem['cpu'] = cpus

        # grab the root
        root = object[self._children][0]
        result = self._extract_important(root, cpus=cpus)
        # and traverse the children
        timers = self._traverse(root, list())

        # merge collected info with report
        report.merge(dict(
            result=result,
            timers=timers,
        ))

        return CollectResult([report])

    def _traverse(self, root, result, path=''):
        path = path + '/' + root['tag']

        item = self._extract_important(root)
        item['path'] = path

        result.append(item)

        if self._children in root:
            for child in root[self._children]:
                self._traverse(child, result, path)

        return result

    @staticmethod
    def _extract_important(child, cpus=1.0):
        sums = {
            'duration': 'cumul-time-sum',
            'call-count': 'call-count-sum',
            'alloc-count': 'memory-alloc-called-sum',
            'dealloc-count': 'memory-dealloc-called-sum',
            'alloc': 'memory-alloc-sum',
            'dealloc': 'memory-dealloc-sum',
        }
        result = dict()
        result.update({k: float(child[v])/cpus for k, v in sums.items()})
        result.update({k: child[k] for k in ['tag', 'file-path', 'function']})
        result['file-line'] = int(child['file-line'])
        return result
