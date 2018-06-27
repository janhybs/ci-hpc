#!/usr/bin/python
# author: Jan Hybs

import os
import json
from utils.logging import logger
from datetime import datetime
from subprocess import check_output
from artifacts.collect.modules import CollectResult, system_info, unwind_report, parse_output


class CollectModule(object):
    system = None   # type: dict
    libs = None     # type: list[dict]
    inited = False  # type: bool

    @classmethod
    def init_collection(cls, path):
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
        cls.libs = [dict(
            name=repo_name,
            branch=branch,
            commit=commit,
            timestamp=timestamp,
            datetime=datetime.fromtimestamp(float(timestamp)),
        )]
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
        opts = cfg.get('generic.artifacts')

        if opts:
            logger.debug('using generic db details from .config.yaml file')
            db = mongo.client.get_database(opts['dbname'])
            files_col = db.get_collection(opts['files_col'])
            reports_col = db.get_collection(opts['reports_col'])
            logger.debug('db: (dbname={dbname}, reports_col={reports_col}, files_col={files_col})', **opts)
        else:
            logger.debug('using generic db wired within the app')
            db = mongo.client.get_database('generic')
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


    def __init__(self):
        self.report = None

    def process_file(self, path):
        # load profiler
        with open(path, 'r') as fp:
            obj = json.load(fp)

        self.report = dict(
            system=CollectModule.system,
            problem=dict(),
            results=obj,
            timer=obj,
            libs=CollectModule.libs,
        )
        return CollectResult([self.report], list())
