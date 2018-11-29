#!/usr/bin/python
# author: Jan Hybs


import itertools
import logging
import os
import shutil

from cihpc.cfg.config import global_configuration
from cihpc.common.processing.pool import WorkerPool, Worker, PoolInt
from cihpc.common.utils import strings
from cihpc.common.utils.datautils import merge_dict, iter_over
from cihpc.common.utils.parallels import extract_cpus_from_worker
from cihpc.common.utils.timer import Timer
from cihpc.core.processing.step_collect import process_step_collect
from cihpc.core.processing.step_git import process_step_git
from cihpc.core.processing.step_shell import process_step_shell, ShellProcessing, ProcessConfigCrate, process_popen


logger = logging.getLogger(__name__)


class ProcessProject(object):
    """
    :type project:  cihpc.core.structures.project.Project
    """

    def __init__(self, project):
        self.project = project
        os.makedirs(self.project.workdir, exist_ok=True)
        os.chdir(self.project.workdir)

    def process(self):
        """
        Method will process entire project
        :return:
        """
        logger.info('preparing project %s', self.project.name)
        # remove old configuration
        shutil.rmtree('tmp.%s' % self.project.name, True)

        # process both sections
        for section in [self.project.install, self.project.test]:
            self.process_section(section)

    def process_section(self, section):
        """
        Method will process every step in a section
        :type section:  ProjectSection
        """
        logger.info('preparing section %s', section.name)
        process_status_log_type = logger.debug
        process_collect_log_type = logger.debug
        # define more complex value so it can be accessed
        # in nested method
        timers_total = PoolInt()

        def step_on_enter(worker: Worker):
            process_status_log_type('%d x %s %s' % (worker.cpus, worker.crate.name, worker.status.name))

        def step_on_exit(worker: Worker):
            process_status_log_type('%d x %s %s' % (worker.cpus, worker.crate.name, worker.status.name))

            if worker.crate.collect:
                project, step, _, format_args = worker.crate.collect
                process_result = worker.result
                collect_result = process_step_collect(
                    project, step, process_result, format_args
                )
                for i in range(len(collect_result.total)):
                    if collect_result.total[i] > 0:
                        process_collect_log_type(
                            'found %d timer(s) in %d file(s)',
                            collect_result.total[i],
                            len(collect_result.items[i])
                        )
                timers_total.value += sum(collect_result.total)

        # clear temp files
        if global_configuration.project_clear_temp:
            tmp_dir = os.path.join(self.project.tmp_workdir, section.ord_name)
            logger.info('removing temp dir %s', tmp_dir)
            shutil.rmtree(tmp_dir, ignore_errors=True)

        for step in section.steps:
            processes: list[ProcessConfigCrate] = list()

            if step.smart_repeat.is_complex() and global_configuration.project_git:
                from cihpc.artifacts.modules import CIHPCReportGit

                logger.info('determining how many repetitions to run from the database')
                step.smart_repeat.load_stats(
                    self.project.name,
                    step.name,
                    CIHPCReportGit.current_commit()
                )

            logger.info('preparing step %s with %d repetitions', step.name, step.repeat)
            for i in range(step.repeat):
                logger.debug('repetition %02d of %02d', i + 1, step.repeat)
                if step.repeat > 1:
                    processes.extend(
                        self.process_step(step, section, indices=['rep-%d-%d' % (i + 1, step.repeat)])
                    )
                elif step.repeat == 1:
                    processes.extend(
                        self.process_step(step, section, indices=[])
                    )
            timers_total.value = 0

            with Timer('step execution', log=logger.info) as execution_timer:
                pool = WorkerPool(processes, step.parallel.cpus, process_popen)
                pool.update_cpu_values(extract_cpus_from_worker)
                pool.thread_event.on_exit.on(step_on_exit)
                pool.thread_event.on_enter.on(step_on_enter)
                # pretty status async logging
                status_thread = pool.log_statuses(format='oneline-grouped')
                # run in serial or parallel
                if step.parallel:
                    logger.info('%d processes will be now executed in parallel' % len(processes))
                    pool.start_parallel()
                else:
                    logger.info('%d processes will be now executed in serial' % len(processes))
                    pool.start_serial()
                status_thread.join()

            try:
                # here we will store additional info to the DB
                # such as how many result we have for each commit
                # or how long the testing took.
                # is this manner, we will have better control over
                # execution for specific commit value, we will now how many results
                # we have for each step, so we can automatically determine how many
                # repetition we need in order to have minimum result available
                if section.name == 'test' and processes and len(processes) > 0:
                    from cihpc.artifacts.modules import CIHPCReport
                    from cihpc.core.db import CIHPCMongo

                    logger.info('%d processes finished, found %d documents' % (len(processes), timers_total()))

                    stats = dict()
                    stats['git'] = CIHPCReport.global_git.copy()
                    stats['system'] = CIHPCReport.global_system.copy()
                    stats['name'] = step.name
                    stats['reps'] = step.repeat
                    stats['docs'] = timers_total()
                    stats['config'] = strings.to_yaml(step.raw_config)
                    stats['duration'] = execution_timer.duration
                    stats['parallel'] = bool(step.parallel)
                    # logger.dump(stats, 'stats')

                    cihpc_mongo = CIHPCMongo.get(self.project.name)
                    insert_result = cihpc_mongo.history.insert_one(stats)
                    logger.debug('DB write acknowledged: %s' % str(insert_result.acknowledged))
                    if insert_result.acknowledged:
                        logger.info('saved stat document to build history')

            except Exception as e:
                logger.exception(str(e))

    def process_step_with_vars(self, step, section, vars, indices=None):
        """
        Method will actually process given step with a given configuration
        Everything else happening before was for this moment

        :type step:     ProjectStep
        :type section:  ProjectSection
        :type indices:  list[str]
        """
        if not step.shell:
            logger.debug('no shell defined in step %s', step.name)
        else:
            shell_processing = ShellProcessing()
            # TODO: move measure block in order to support parallel processing
            # if step.measure:
            #     process_step_measure(step, step.measure, shell_processing)

            return process_step_shell(self.project, section, step, vars, shell_processing, indices)

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

    def process_step(self, step, section, indices=list()):
        """
        :type step:     ProjectStep
        :type section:  ProjectSection
        """

        processes = list()  # type: list[ProcessConfigCrate]

        if not step.enabled:
            logger.debug('step %s is disabled', step.name)
            return

        logger.debug('processing step %s (%s)', step.name, indices)

        if not step.git:
            logger.debug('no repos setup')
        else:
            process_step_git(step.git, self.project.global_args)

        if step.variables:
            logger.debug('found %d build matrices', len(step.variables))

            len_variables = len(step.variables)
            cur_variables = 0
            
            for matrix_section in step.variables:
                cur_variables += 1
                variables = self.expand_variables(matrix_section)

                for vars, current, total in iter_over(variables):
                    proc_indices = indices.copy() + [
                        'var-%d-%d' % (cur_variables, len_variables),
                        'cfg-%d-%d' % (current + 1, total),
                    ]
                    
                    vars = merge_dict(vars, dict(
                        __total__=total,
                        __current__=current + 1,
                        __unique__=self.project.unique(),
                    ))
                    process_result = self.process_step_with_vars(step, section, vars, proc_indices)

                    processes.append(process_result)
                    # # artifact collection
                    # if step.collect:
                    #     format_args = merge_dict(
                    #         self.project.global_args,
                    #         vars,
                    #     )
                    #     process_step_collect(self.project, step, process_result, format_args)
        else:
            logger.info('processing step %s without variables', step.name)
            process_result = self.process_step_with_vars(step, section, None, indices.copy())
            processes.append(process_result)

        return processes

    @classmethod
    def configure(cls, o, d):
        for k in o:
            if type(o[k]) is str:
                o[k] = o[k].format(**d)
            elif type(o[k]) is dict:
                o[k] = cls.configure(o[k], d)
        return o
