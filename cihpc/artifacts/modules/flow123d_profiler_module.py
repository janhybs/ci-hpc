#!/usr/bin/python
# author: Jan Hybs


import json
import os
import re

from cihpc.artifacts.modules import CollectResult, AbstractCollectModule, CIHPCReport


class CollectModule(AbstractCollectModule):
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

            # merge collected info with report
            report.merge(dict(
                result=result,
                timers=timers,
            ))

        return CollectResult([report])

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
