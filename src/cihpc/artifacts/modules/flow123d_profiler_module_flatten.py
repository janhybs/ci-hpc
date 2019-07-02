#!/usr/bin/python
# author: Jan Hybs


import re
import uuid

import cihpc.artifacts.base as artifacts_base


class CollectModule(artifacts_base.AbstractCollectModule):
    _children = 'children'

    def process(self, object, from_file=None):
        # initial report
        report = artifacts_base.CIHPCReport()
        run_id = uuid.uuid4().hex

        # link timers together
        if 'index' not in report:
            report['index'] = dict()
        report['index']['run_id'] = run_id

        if object:
            # grab version while we're at it
            report.git['version'] = object['program-version']
            # grab task size as well
            report.problem['task-size'] = int(object['task-size'])

            # get cpu
            cpus = float(object['run-process-count'])
            report.problem['cpus'] = cpus

            # grab the root
            root = object[self._children][0]
            result = self._extract_important(root, cpus=cpus)
            # and traverse the children
            timers = self._traverse(root, list())

            run_reports = list()

            # merge collected info with report
            report.merge(dict(
                result=dict(),
                timers=[],
            ))

            for timer in timers:
                timer_report = report.copy()
                timer_report['result'] = timer
                timer_report['index']['frame'] = timer_report['result']['name']
                run_reports.append(timer_report)

            return artifacts_base.CollectResult(run_reports)

        raise ValueError(f'Given object does not contain any useful data {object}')

    @classmethod
    def _normalise_tag_name(cls, tag: str):
        return re.sub('[_-]+', '-',
                      re.sub("([a-z])([A-Z])", "\g<1>-\g<2>", tag) \
                      .replace('::', '-') \
                      .replace(' ', '-').lower()
                      )

    def _traverse(self, root, result, path=''):
        path = path + '/' + self._normalise_tag_name(root['tag'])

        item = self._extract_important(root)
        item['path'] = path

        result.append(item)

        if self._children in root:
            for child in root[self._children]:
                self._traverse(child, result, path)

        return result

    @classmethod
    def _extract_important(cls, child, cpus=1.0):
        sums = {
            'duration'   : 'cumul-time-sum',
            'executed'   : 'call-count-sum',
            'cnt-alloc'  : 'memory-alloc-called-sum',
            'cnt-dealloc': 'memory-dealloc-called-sum',
            'mem-alloc'  : 'memory-alloc-sum',
            'mem-dealloc': 'memory-dealloc-sum',
        }
        result = dict()
        result.update({k: float(child[v]) / cpus for k, v in sums.items()})
        result.update({k: child[k] for k in ['file-path', 'function']})

        result['name'] = cls._normalise_tag_name(child['tag'])
        result['file-line'] = int(child['file-line'])
        result['dur-ratio'] = float(child['cumul-time-min']) / float(child['cumul-time-max'])
        return result
