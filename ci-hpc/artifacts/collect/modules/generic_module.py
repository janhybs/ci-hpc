#!/usr/bin/python
# author: Jan Hybs

import os
import json
from utils.logging import logger
from datetime import datetime
from subprocess import check_output
from artifacts.collect.modules import CollectResult, system_info, unwind_report, parse_output, CIHPCReportGit, \
    CIHPCReport
from artifacts.db.mongo import CIHPCMongo


class CollectModule(object):
    system = None   # type: dict
    git = None      # type: dict
    inited = False  # type: bool

    @classmethod
    def init_collection(cls, path):
        """
        Given path to a dir or file located within git repository, will try to determine branch/commit
        :param path:
        """
        if cls.inited:
            return

        logger.debug('getting git information')
        root = path
        if os.path.isfile(path):
            root = os.path.dirname(path)

        repo_name = parse_output(
            check_output('basename `git rev-parse --show-toplevel`', shell=True, cwd=root)
        )
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
        cls.git = CIHPCReportGit()
        cls.git.update(
            dict(
                name=repo_name,
                branch=branch,
                commit=commit,
                timestamp=timestamp,
                datetime=datetime.fromtimestamp(float(timestamp)),
            )
        )
        cls.inited = True

    @classmethod
    def add_extra(cls, extra):
        """
        Method adds extra arguments to the base object
        :param extra:
        :return:
        """
        if extra:
            cls.system.update(extra)

    def save_to_db(self, collect_results):
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
        cihpc_mongo = CIHPCMongo.get(self.project_name)

        results = list()
        for item in collect_results:

            # save logs first
            if item.logs and item.items:
                log_ids = cihpc_mongo.files.insert_many(item.logs).inserted_ids
                logger.debug('inserted %d files', len(log_ids))
                item.update(log_ids)

            # insert rest to db
            if item.items:
                results.append(cihpc_mongo.reports.insert_many(item.items))
        logger.debug('inserted %d reports', len(results))
        return results

    def __init__(self, project_name):
        self.report = None
        self.project_name = project_name

    def process_file(self, path):
        # load profiler
        with open(path, 'r') as fp:
            obj = json.load(fp)

        self.report = CIHPCReport()
        self.report.update(
            dict(
                system=CollectModule.system,
                git=CollectModule.git,
            )
        )
        self.report.update(obj)
        # items = unwind_report(self.report)
        return CollectResult([self.report], list())
