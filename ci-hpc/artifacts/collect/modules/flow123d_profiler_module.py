#!/usr/bin/python
# author: Jan Hybs


import hashlib
import json
import os
import datetime
import re
import uuid
from subprocess import check_output

from utils.logging import logger
from artifacts.collect.modules import CollectResult, system_info, unwind_report


def parse_output(out, line=None):
    lines = out.decode().strip().splitlines()
    if line:
        for l in lines:
            if l.startswith(line):
                return l[len(line):].replace('"', '')
    return lines[0].replace('"', '')


class CollectModule(object):
    system = None   # type: dict
    libs = None     # type: list[dict]
    inited = False  # type: bool

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

    @classmethod
    def init(cls, path):
        """
        Given path to a dir or file located within git repository, will try to determine branch/commit
        :param path:
        """
        if cls.inited:
            return

        logger.info('getting git information')
        root = path
        if os.path.isfile(path):
            root = os.path.dirname(path)

        branch = parse_output(
            check_output('git symbolic-ref --short -q HEAD', shell=True, cwd=root)
        )
        commit = parse_output(
            check_output('git rev-parse HEAD', shell=True, cwd=root)
        )
        timestamp = int(parse_output(
                check_output('git show -s --format=%%ct %s' % commit, shell=True, cwd=root)
        ))
        logger.info('current git index at (branch=%s, commit=%s)', branch, commit)

        cls.system = system_info()
        cls.libs = [dict(
            name='flow123d',
            branch=branch,
            commit=commit,
            timestamp=timestamp,
            datetime=datetime.datetime.fromtimestamp(float(timestamp)),
        )]
        cls.inited = True

    def __init__(self):
        self.report = None
        self.reports = None
        self.extra = None

    @classmethod
    def try2extract_from_dummy(cls, dir_name):
        """Method will try create dummy profiler and estimate cores and test name"""
        pcs = dir_name.split('.')
        if len(pcs) == 3:
            name, cpu, el = pcs
            pcs = el.split('_')
            el = int(pcs[1]) if len(pcs) == 3 else int(pcs[0])
        elif len(pcs) == 2:
            name, cpu = pcs
            el = 0
        else:
            name = dir_name
            cpu = 0
            el = 0

        return {
            'task-size': el,
            'run-process-count': int(cpu),
            'children': [
                {
                    'tag': 'Whole Program'
                }
            ]
        }

    def _convert_fields(self, obj, fields, method):
        """
        Recursively will convert given field props to a given type
        :param obj:
        :param fields:
        :param method:
        :return:
        """
        for key in obj:
            for f in fields:
                if f.match(key):
                    obj[key] = method(obj[key])

        if self._children in obj:
            for child in obj[self._children]:
                self._convert_fields(child, fields, method)

    @staticmethod
    def _parse_date(s):
        """
        :rtype: datetime.datetime
        """
        return datetime.datetime.strptime(s, '%m/%d/%y %H:%M:%S').timestamp()

    def process_file(self, path):

        # load profiler
        with open(path, 'r') as fp:
            obj = json.load(fp)

        if not obj:
            obj = self.try2extract_from_dummy(os.path.basename(os.path.dirname(path)))

        # load status.json if possible
        status_file = os.path.join(os.path.dirname(path), 'runtest.status.json')
        status = dict(returncode=0)
        if os.path.exists(status_file):
            with open(status_file, 'r') as fp:
                status = json.load(fp)

        self._convert_fields(obj, self._ints,   int)
        self._convert_fields(obj, self._floats, float)
        self._convert_fields(obj, self._dates, self._parse_date)

        parts = path.split('/')
        problem, start = self._get_base(obj)
        problem['test-name'] = parts[-4]
        problem['case-name'] = parts[-2].split('.')[0]
        problem['uuid'] = uuid.uuid4().hex   # so we determine which frame is part of which run
        problem['application'] = 'flow123d'
        problem['cpu'] = problem['run-process-count']
        del problem['run-process-count']
        problem.update(status)
        problem.update(problem)

        timers = self._unwind(start, list())
        results = timers[0]

        self.report = dict(
            system=CollectModule.system,
            problem=problem,
            results =results,
            timers=timers,
            libs=CollectModule.libs,
        )
        self.reports = unwind_report(self.report)

        collect_result = CollectResult(
            items=self.reports,
            logs=[
                os.path.join(os.path.dirname(path), 'job_output.log'),
                os.path.join(os.path.dirname(path), 'flow123.0.log')
            ],
            log_folder=os.path.dirname(path),
        )

        return collect_result

    def _unwind(self, obj, result, path=''):
        """
        Method will convert nested structure to flatten one
        :type obj:    dict
        :type path:   str
        :type result: list
        """
        # empty obj
        if not obj:
            return result

        item = obj.copy()
        if self._children in item:
            del item[self._children]

        tag = item['tag']
        new_path = path + '/' + tag
        indices = dict()
        indices['tag'] = tag
        indices['tag_hash'] = self._md5(tag)
        indices['path'] = new_path
        indices['path_hash'] = self._md5(new_path)
        indices['parent'] = path
        indices['parent_hash'] = self._md5(path)
        item.update(indices)

        result.append(item)

        if self._children in obj:
            for o in obj[self._children]:
                self._unwind(o, result, new_path)
        return result

    def _get_base(self, obj):
        """
        :rtype: (dict, dict)
        :type obj: dict
        """
        if not obj or self._children not in obj:
            return {}, {}

        base = obj.copy()
        if self._children in base:
            del base[self._children]
            return base, obj[self._children][0]

    @classmethod
    def _md5(cls, s):
        return hashlib.md5(s.encode()).hexdigest()

    @classmethod
    def save_to_db(cls, collect_results):
        """
        Method will insert results into db
        it will use either static values for the dbname and collection
        or if flow123d.artifacts is set, will user values
            - flow123d.artifacts.dbname:        for a database name
            - flow123d.artifacts.files_col:     for a collection containing files
            - flow123d.artifacts.reports_col:   for a collection containing reports
        :type collect_results: list[CollectResult]
        """
        logger.info('saving %d profile.json files to database', len(collect_results))

        from utils.config import Config as cfg
        from artifacts.db.mongo import Mongo

        mongo = Mongo()
        opts = cfg.get('flow123d.artifacts')

        if opts:
            logger.debug('using flow123d db details from .config.yaml file')
            db = mongo.client.get_database(opts['dbname'])
            files_col = db.get_collection(opts['files_col'])
            reports_col = db.get_collection(opts['reports_col'])
            logger.debug('db: (dbname={dbname}, reports_col={reports_col}, files_col={files_col})', **opts)
        else:
            logger.debug('using flow123d db wired within the app')
            db = mongo.client.get_database('flow123d')
            files_col = db.get_collection('fs')
            reports_col = db.get_collection('reports')
            logger.debug('db: (dbname=flow123d, reports_col=reports, files_col=fs)', **opts)

        results = list()
        for item in collect_results:

            # save logs first
            if item.logs and item.items:
                log_ids = files_col.insert_many(item.logs).inserted_ids
                logger.debug('inserted %d files', len(log_ids))
                item.update(log_ids)

            # insert rest to db
            if item.items:
                results.append(reports_col.insert_many(item.items))
        logger.debug('inserted %d reports', len(results))
        return results

    @classmethod
    def add_extra(cls, extra):
        """
        Method adds extra arguments to the base object
        :param extra:
        :return:
        """
        if extra:
            cls.system.update(extra)