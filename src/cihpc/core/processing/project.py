#!/usr/bin/python
# author: Jan Hybs
from typing import List

from loguru import logger
import os
import threading

from cihpc.common.processing.pool import LogStatusFormat, WorkerPool
from cihpc.common.utils.datautils import merge_dict
from cihpc.common.utils.parallels import extract_cpus_from_worker
from cihpc.common.utils.timer import Timer
from cihpc.core.processing.stage import ProcessStage
import cihpc.common.utils.progress as progress

import cihpc.artifacts.base as artifacts_base
from cihpc.core.structures.project_stage import ProjectStage
import cihpc.core.db as db
from cihpc.exceptions.exec_error import OnError


class ProcessProject(object):
    """
    :type project:  cihpc.core.structures.project.Project
    """

    def __init__(self, project, initialize_repository=True):
        self.project = project
        self.definition = project
        os.makedirs(self.project.workdir, exist_ok=True)
        os.chdir(self.project.workdir)

        if self.project.use_database:
            db.CIHPCMongo.set_default(
                db.CIHPCMongo.get(self.project.name)
            )

        if initialize_repository:
            main_repo = self.project.git.main_repo
            if main_repo:
                main_repo.initialize()
                logger.info(f'Repo {main_repo.name} currently at {main_repo.index_info()}')
                # register info about git to report

                artifacts_base.CIHPCReport.global_git.update(
                    name=main_repo.name,
                    branch=main_repo.branch,
                    commit=main_repo.commit,
                )

            for dep in self.project.git.deps.values():
                if dep:
                    dep.initialize()
                    logger.info(f'Repo {dep.name} currently at {dep.index_info()}')

    def get_stage_by_name(self, name: str):
        for stage in self.project.stages:
            if stage and stage.name == name:
                return stage
        return None

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

    def get_stage_variable_stats(self, stage: ProjectStage):
        variables = self.project.global_args
        variables['__stage__'] = stage.stage_args

        for i, v in enumerate(stage.variables.expand()):
            vars = merge_dict(variables, v)
            index: dict = ProcessStage.expand_index(stage.index, vars)
            repeat = ProcessStage.determine_number_of_repetitions(index, stage.smart_repeat)
            yield repeat, index

    def create_process_stage_threads(self, stage:ProjectStage) -> List[ProcessStage]:
        return ProcessStage.create(self.project, stage)

    def process_stage(self, stage: ProjectStage):
        return self._process_stage_threads(
            stage,
            self.create_process_stage_threads(stage)
        )

    def _process_stage_threads(self, stage: ProjectStage, threads: List[ProcessStage]):
        with Timer(stage.ord_name) as timer:
            pool = WorkerPool(cpu_count=stage.parallel.cpus, threads=threads)
            pool.update_cpu_values(extract_cpus_from_worker)

            if stage.parallel:
                logger.info(f'{len(threads)} job(s) will be now executed in parallel\n'
                            'allocated cores: {stage.parallel.cpus}')
            else:
                logger.info(f'{len(threads)} job(s) will be now executed in serial')

            default_status = pool.get_statuses(LogStatusFormat.ONELINE)
            progress_line = progress.Line(total=len(threads), desc='%s: %s' % (stage.ord_name, default_status), tty=False)

            def update_status_enter(worker: ProcessStage):
                progress_line.desc = '%02d-%s: %s ' % (
                    stage.ord,
                    worker.debug_name if worker else '?',
                    pool.get_statuses(LogStatusFormat.ONELINE)
                )
                progress_line.update(0)

            def update_status_exit(worker: ProcessStage):
                progress_line.desc = '%02d-%s: %s ' % (
                    stage.ord,
                    worker.debug_name if worker else '?',
                    pool.get_statuses(LogStatusFormat.ONELINE)
                )
                progress_line.update()

            pool.thread_event.on_exit.on(update_status_exit)
            pool.thread_event.on_enter.on(update_status_enter)

            # run in serial or parallel
            progress_line.start()
            pool.start()
            progress_line.close()

            if pool.terminate:
                logger.error('Caught pool terminate signal!')
                if not pool.exception or pool.exception.on_error is OnError.EXIT:
                    logger.error(f'Exiting application with 1')
                    exit(1)

                if pool.exception.on_error is OnError.BREAK:
                    return False

        timers_total = sum([sum(x.collect_result.total) for x in threads if x.collect_result])
        logger.info(f'{len(threads)} processes finished, found {timers_total} documents')
        return True

    @classmethod
    def configure(cls, o, d):
        for k in o:
            if type(o[k]) is str:
                o[k] = o[k].format(**d)
            elif type(o[k]) is dict:
                o[k] = cls.configure(o[k], d)
        return o
