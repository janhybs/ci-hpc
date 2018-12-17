#!/usr/bin/python
# author: Jan Hybs


import itertools
import logging
import os
import sys
import threading


from cihpc.common.processing.pool import LogStatusFormat, WorkerPool, SimpleWorker
from cihpc.common.utils import strings
from cihpc.common.utils.parallels import extract_cpus_from_worker
from cihpc.common.utils.timer import Timer
from cihpc.core.db import CIHPCMongo
from cihpc.core.processing.stage import ProcessStage
import cihpc.common.utils.progress as progress


logger = logging.getLogger(__name__)


class ProcessProject(object):
    """
    :type project:  cihpc.core.structures.project.Project
    """

    def __init__(self, project):
        self.project = project
        self._mongo = CIHPCMongo.get(self.project.name) if self.project.use_database else None
        os.makedirs(self.project.workdir, exist_ok=True)
        os.chdir(self.project.workdir)

    @property
    def mongo(self):
        if not self._mongo:
            self._mongo = CIHPCMongo.get(self.project.name)
        return self._mongo

    def process(self):
        """
        Method will read configuration and prepare threads, which will
        perform given action
        Returns
        -------

        list[threading.Thread]
        """
        for stage in self.project.stages:
            if stage:
                threads = ProcessStage.create(self.project, stage)
                self._process_stage_threads(stage, threads)

    def process_stage(self, stage):
        threads = ProcessStage.create(self.project, stage)
        self._process_stage_threads(stage, threads)

    def _process_stage_threads(self, stage, threads):
        with Timer(stage.ord_name) as timer:
            pool = WorkerPool(cpu_count=stage.parallel.cpus, threads=threads)
            pool.update_cpu_values(extract_cpus_from_worker)

            if stage.parallel:
                logger.info('%d job(s) will be now executed in parallel\n'
                            'allocated cores: %d' % (len(threads), stage.parallel.cpus))
            else:
                logger.info('%d job(s) will be now executed in serial' % len(threads))

            default_status = pool.get_statuses(LogStatusFormat.ONELINE)
            progress_line = progress.Line(total=len(threads), desc='%s: %s' % (stage.ord_name, default_status))

            def update_status(worker: SimpleWorker):
                progress_line.desc = '%s: %s' % (stage.ord_name, pool.get_statuses(LogStatusFormat.ONELINE))
                progress_line.update()

            pool.thread_event.on_exit.on(update_status)

            # run in serial or parallel
            progress_line.start()
            pool.start()
            progress_line.close()

        timers_total = sum([sum(x.collect_result.total) for x in threads if x.collect_result])
        if timers_total:
            self._save_stats(stage, threads, timers_total, timer.duration)

    def _save_stats(self, stage, threads, timers_total, duration):
        try:
            # here we will store additional info to the DB
            # such as how many result we have for each commit
            # or how long the testing took.
            # is this manner, we will have better control over
            # execution for specific commit value, we will now how many results
            # we have for each step, so we can automatically determine how many
            # repetition we need in order to have minimum result available
            from cihpc.artifacts.modules import CIHPCReport
            from cihpc.core.db import CIHPCMongo

            logger.info('%d processes finished, found %d documents' % (len(threads), timers_total))

            stats = dict()
            stats['git'] = CIHPCReport.global_git.copy()
            stats['system'] = CIHPCReport.global_system.copy()
            stats['name'] = stage.name
            stats['reps'] = stage.repeat
            stats['docs'] = timers_total
            stats['config'] = strings.to_yaml(stage.raw_config)
            stats['duration'] = duration
            stats['parallel'] = bool(stage.parallel)
            # logger.dump(stats, 'stats')

            cihpc_mongo = CIHPCMongo.get(self.project.name)
            insert_result = cihpc_mongo.history.insert_one(stats)
            logger.debug('DB write acknowledged: %s' % str(insert_result.acknowledged))
            if insert_result.acknowledged:
                logger.info('saved stat document to build history')

        except Exception as e:
            logger.exception(str(e))

    @staticmethod
    def expand_variables(section):
        def extract_first(iterator):
            return next(iter(iterator))

        def ensure_list(o):
            if isinstance(o, list):
                return o
            return [o]

        section_name = extract_first(section.keys())
        variables = extract_first(section.values())
        names = [extract_first(y.keys()) for y in variables]

        if section_name == 'values':
            total = max([len(ensure_list(extract_first(y.values()))) for y in variables])
            values = list()
            for y in variables:
                value = extract_first(y.values())
                if isinstance(value, list):
                    values.append(value)
                else:
                    values.append(list(itertools.repeat(value, total)))

            product = [{names[v_j]: values[v_j][v_i] for v_j in range(len(names))} for v_i in range(total)]
            logger.debug('created value matrix with %d configurations', len(product))
        elif section_name == 'matrix':

            values = [ensure_list(extract_first(y.values())) for y in variables]
            product = list(dict(zip(names, x)) for x in itertools.product(*values))
            logger.debug('created build matrix with %d configurations', len(product))
        else:
            raise Exception('Invalid variable type %s' % section_name)

        return product

    @classmethod
    def configure(cls, o, d):
        for k in o:
            if type(o[k]) is str:
                o[k] = o[k].format(**d)
            elif type(o[k]) is dict:
                o[k] = cls.configure(o[k], d)
        return o
