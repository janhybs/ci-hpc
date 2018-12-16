#!/bin/python3
# author: Jan Hybs

import logging
import os
import subprocess as sp
import yaml

from cihpc.cfg.config import global_configuration
from cihpc.core.processing.step_collect import process_step_collect
from cihpc.core.processing.step_shell import ProcessStepResult

from cihpc.common.utils.files.dynamic_io import DynamicIO


logger = logging.getLogger(__name__)

from cihpc.common.processing.pool import SimpleWorker
from cihpc.common.utils.datautils import merge_dict
from cihpc.core.processing.step_cache import ProcessStepCache
from cihpc.cfg.cfgutil import configure_string
from cihpc.common.utils.files.temp_file import TempFile
from cihpc.common.utils.parallels import parse_cpu_property
from cihpc.core.processing.step_git import process_step_git


class ProcessStage(SimpleWorker):
    """
    Parameters
    ----------
    stage: cihpc.core.structures.project_stage.ProjectStage
        stage which is this instance bound to

    variables: dict
        optional variables for the sub stage

    _cache: ProcessStepCache
    """

    @classmethod
    def create(cls, project, stage, variables=None):
        """
        Parameters
        ----------
        stage: cihpc.core.structures.project_stage.ProjectStage
            stage which is this instance bound to

        variables: dict
            optional variables for the sub stage

        """

        if not stage:
            return []

        variables = variables or project.global_args
        if stage.smart_repeat.is_complex() and global_configuration.project_git:
            from cihpc.artifacts.modules import CIHPCReportGit

            logger.debug('determining how many repetitions to run from the database')
            stage.smart_repeat.load_stats(
                project.name,
                stage.name,
                CIHPCReportGit.current_commit()
            )

        result = list()
        for j in range(stage.repeat):
            items = list(stage.variables.items())
            total = len(items)
            if total:
                for i, v in enumerate(items):
                    vars = merge_dict(variables, v)
                    worker = ProcessStage(project, stage, vars)
                    worker.name_prefix = '%02d-%02d-' % (i + 1, total)
                    result.append(worker)
            else:
                worker = ProcessStage(project, stage, variables)
                result.append(worker)
        return result

    def __init__(self, project, stage, variables):
        """
        Parameters
        ----------
        project: cihpc.core.structures.project.Project
            stage which is this instance bound to

        stage: cihpc.core.structures.project_stage.ProjectStage
            stage which is this instance bound to

        variables: dict
            optional variables for the sub stage

        """
        super(ProcessStage, self).__init__()
        self.stage = stage
        self.variables = variables
        self.project = project

        self.name = stage.name
        self.name_prefix = ''

        self._shell_result = None
        self._cache = None
        self.collect_result = None

        # here we try to determine how many cpus we want to use in this step
        # based on a cpu-prop value
        if self.stage.parallel and self.stage.parallel.prop:
            cpu_prop_conf = configure_string(self.stage.parallel.prop, self.variables)
            cpu_prop = parse_cpu_property(cpu_prop_conf)
            self.variables.update(dict(__cpu__=cpu_prop))

    @property
    def ord_name(self):
        return self.name_prefix + self.name

    @property
    def pretty_name(self):
        return '{self.cpus}x{self.ord_name}({self.status})'.format(
            self=self
        )

    def __repr__(self):
        return '{self.__class__.__name__}({self.ord_name})'.format(
            self=self
        )

    def _run(self):
        project = self.project
        step = self.stage

        if self._cache_init():
            return True

        self._git_init()

        self.variables = merge_dict(
            project.global_args,
            self.variables,
        )

        if step.shell:
            tmp_dir_lst = [
                project.tmp_workdir,
                step.ord_name,
                self.ord_name,
            ]

            # convert list to file path string
            tmp_dir = os.path.join(*tmp_dir_lst)

            # create dir
            os.makedirs(tmp_dir, exist_ok=True)

            # the main script which will be executed, either using bash or with the help of a container
            tmp_sh = TempFile(os.path.join(tmp_dir, 'shell.sh'))
            tmp_cont = TempFile(os.path.join(tmp_dir, 'cont.sh'))

            # ---------------------------------------------------------------------

            args = self._generate_files(self.variables, tmp_sh, tmp_cont)
            self._shell_result = self._run_script(args)

        if self._cache:
            self._cache_save()

        if self.stage.collect:
            self.collect_result = self._collect()

    def _generate_files(self, format_args, tmp_sh, tmp_cont):
        project = self.project
        step = self.stage
        vars = self.variables

        with tmp_sh:
            tmp_sh.write_shebang()

            if vars:
                try:
                    vars_json = yaml.dump(vars, default_flow_style=False)
                except:
                    vars_json = str(vars)

                tmp_sh.write_section('CONFIGURATION', '\n'.join(['# ' + x for x in vars_json.splitlines()]))

            if project.init_shell:
                configured = configure_string(project.init_shell, format_args)
                tmp_sh.write_section('INIT SHELL', configured)

            configured = configure_string(step.shell, format_args)
            tmp_sh.write_section('STEP SHELL', configured)
            args = ['bash', tmp_sh.path]

        if step.container:
            with tmp_cont:
                tmp_cont.write_shebang()
                tmp_cont.write(configure_string(step.container.exec % tmp_sh.path, format_args))
            args = ['bash', tmp_cont.path]
        return args

    def _run_script(self, args):
        io = DynamicIO(self.stage.output)
        result = ProcessStepResult()

        with io:
            if io.is_writable():
                io.fp.write('=' * 80 + '\n')
                io.fp.write(' '.join(args) + '\n')
                io.fp.write('=' * 80 + '\n')
                io.fp.flush()

            logger.debug('running ' + ' '.join(args))
            process = sp.Popen(args, stdout=io.fp, stderr=sp.STDOUT)
            result.process = process

            with process:
                result.returncode = process.wait()
                if result.returncode == 0:
                    logger.debug('ok [%d] ended with %d' % (process.pid, result.returncode))
                else:
                    logger.warning('process [%d] ended with %d' % (process.pid, result.returncode))

            if io.is_writable():
                io.fp.write('-' * 80 + '\n')
                io.fp.flush()
        result.output = getattr(io.opener, 'output', None)
        return result

    def _git_init(self):
        # checkout first
        if self.stage.gits:
            process_step_git(self.stage.gits, self.variables)

    def _cache_save(self):
        if not self._cache.exists():
            logger.debug('saving cache %s to %s' % (self.stage, self._cache.location))
            self._cache.save()

    def _cache_init(self):
        # try to use cache if possible
        if self.stage.cache:
            self._cache = ProcessStepCache(self.stage.cache, self.stage.gits, self.variables)

        if self._cache and self._cache.exists():
            logger.debug('skipped sage %s, using cache %s' % (self.stage, self._cache.value))
            self._cache.restore()
            return True

    def _collect(self):
        collect_result = process_step_collect(
            self.project, self.stage, self._shell_result, self.variables
        )
        for i in range(len(collect_result.total)):
            if collect_result.total[i] > 0:
                logger.debug(
                    'found %d timer(s) in %d file(s)',
                    collect_result.total[i],
                    len(collect_result.items[i])
                )
        return collect_result
