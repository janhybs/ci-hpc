#!/bin/python3
# author: Jan Hybs

from loguru import logger
import os
import subprocess as sp

from cihpc.core.processing.step_collect import process_step_collect
from cihpc.core.processing.step_shell import ProcessStepResult

from cihpc.common.utils.files.dynamic_io import DynamicIO


from cihpc.common.processing.pool import SimpleWorker
from cihpc.common.utils.datautils import merge_dict
from cihpc.core.processing.step_cache import ProcessStepCache
from cihpc.cfg.cfgutil import configure_string, configure_object
from cihpc.common.utils.files.temp_file import TempFile
from cihpc.common.utils.parallels import parse_cpu_property
import cihpc.core.db as db


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
        variables['__stage__'] = stage.stage_args
        result = list()

        items = list(stage.variables.expand())
        total = len(items)
        for i, v in enumerate(items):
            vars = merge_dict(variables, v)
            current_index = cls.expand_index(stage.index, vars)
            repeat = cls.determine_number_of_repetitions(current_index, stage.smart_repeat)

            for j in range(repeat):
                prefixes = [
                    'conf-%02d--reps-%02d-' % (i + 1, j + 1),
                ]

                worker = ProcessStage(project, stage, vars)
                worker.name_prefix = os.path.join(*prefixes)
                result.append(worker)

        return result

    @staticmethod
    def expand_index(index, variables):
        if index:
            return configure_object(index, variables)
        return dict()

    @staticmethod
    def determine_number_of_repetitions(index, spec):
        """

        Parameters
        ----------
        index: dict
        spec: cihpc.core.structures.project_step_repeat.ProjectStepRepeat

        Returns
        -------
        int
        """

        min_repeat = spec.value if spec else 1
        if not min_repeat or min_repeat < 1:
            min_repeat = 1

        if not index or not spec.is_complex():
            return min_repeat

        connection = db.CIHPCMongo.get_default()
        if connection:
            query = {f'index.{key}': value for key, value in index.items()}
            total = connection.reports.find(query).count()

            if total == 0:
                repeat = min_repeat
            elif total < min_repeat:
                repeat = min_repeat - total
            else:
                repeat = 0

            logger.info(f'index: {index}')
            logger.info(f'query: db.{connection.reports.name}.find({query})')
            logger.info(f'required: {min_repeat}, found: {total}, repetition: {repeat}')

            return repeat

        return min_repeat

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
        self.current_index = None

        if self.stage.index:
            self.current_index = configure_object(self.stage.index, self.variables)

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
    def debug_name(self):
        props = ['benchmark', 'mesh', 'cpu']
        rest = ','.join(['%s=%s' % (x, str(self.variables.get(x, '?'))) for x in props if x in self.variables])
        if rest:
            rest = ', ' + rest
        return '{self.name} {self.cpus}x({self.status.name}{rest})'.format(
            self=self,
            rest=rest
        )

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

        self.variables = merge_dict(
            project.global_args,
            self.variables,
        )

        if step.shell:
            tmp_dir_lst = [
                project.tmp_workdir,
                step.ord_name,
            ]

            # convert list to file path string
            tmp_dir = os.path.join(*tmp_dir_lst)

            # create dir
            os.makedirs(tmp_dir, exist_ok=True)

            # the main script which will be executed, either using bash or with the help of a container
            # tmp_sh = TempFile(os.path.join(tmp_dir, 'shell.sh'))
            # tmp_cont = TempFile(os.path.join(tmp_dir, 'cont.sh'))

            tmp_sh = TempFile(os.path.join(tmp_dir, self.ord_name + '--shell.sh'))
            tmp_cont = TempFile(os.path.join(tmp_dir, self.ord_name + '--cont.sh'))

            # ---------------------------------------------------------------------

            args = self._generate_files(self.variables, tmp_sh, tmp_cont)
            self._shell_result = self._run_script(args)

            if self._shell_result.returncode != 0:
                if self.stage.on_error in ('exit', 'terminate', 'end', 'break'):
                    logger.error(f'Process ended with {self._shell_result.returncode} and on-error is set to {self.stage.on_error}')
                    return False

        if self._cache:
            self._cache_save()

        if self.stage.collect:
            self.collect_result = self._collect()

        return True

    def _generate_files(self, format_args, tmp_sh, tmp_cont):
        project = self.project
        step = self.stage
        vars = self.variables

        with tmp_sh:
            tmp_sh.write_shebang()

            if vars:
                try:
                    vars_json = '\n'.join([f'{k}: {v}' for k,v in vars.items() if not str(k).startswith('!')])
                except Exception as e:
                    vars_json = str(vars)

                tmp_sh.write_section('CONFIGURATION', '\n'.join(['# ' + x for x in vars_json.splitlines()]))

            if project.init_shell:
                configured = configure_string(project.init_shell, format_args)
                tmp_sh.write_section('INIT SHELL', configured)

            configured = configure_string(step.shell, format_args)
            tmp_sh.write_section('STEP SHELL', configured)
            args = ['bash', tmp_sh.path]
        # logger.warning(tmp_sh.content)

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

    def _cache_save(self):
        if not self._cache.exists():
            logger.debug('saving cache %s to %s' % (self.stage, self._cache.location))
            self._cache.save()

    def _cache_init(self):
        # try to use cache if possible
        if self.stage.cache:
            self._cache = ProcessStepCache(self.stage.cache, self.stage.gits, self.variables)

        if self._cache and self._cache.exists():
            logger.debug('skipped stage %s, using cache %s' % (self.stage, self._cache.location))
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
