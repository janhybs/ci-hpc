#!/usr/bin/python
# author: Jan Hybs

import logging
import os
import subprocess as sp
from time import time

import yaml

from cihpc.cfg.cfgutil import configure_string
from cihpc.common.utils.datautils import merge_dict
from cihpc.common.utils.events import EnterExitEvent
from cihpc.common.utils.files.dynamic_io import DynamicIO
from cihpc.common.utils.files.temp_file import TempFile
from cihpc.common.utils.parallels import parse_cpu_property


logger = logging.getLogger(__name__)


class ShellProcessing(object):
    def __init__(self):
        self.init = EnterExitEvent('Init')
        self.shell = EnterExitEvent('Shell')
        self.process = EnterExitEvent('Process')


class ProcessStepResult(object):
    """
    :type process: subprocess.Popen
    :type output:  str
    """

    def __init__(self):
        self.process = None
        self.duration = None
        self.shell_duration = None
        self.returncode = None
        self.start_time = None
        self.end_time = None

        self.output = None
        self.error = None

    def __enter__(self):
        self.start_time = time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time()
        self.duration = self.end_time - self.start_time
        return False

    def __repr__(self):
        return 'ProcessStepResult({self.process}, {self.duration})'.format(self=self)

    def to_json(self):
        return dict(
            start_time=self.start_time,
            end_time=self.end_time,
            returncode=self.returncode,
            duration=self.duration,
            output=self.output,
            error=self.error,
            shell_duration=self.shell_duration,
        )


def process_step_shell(project, section, step, vars, shell_processing, indices):
    """
    Function will execute shell from given step using specific vars in the process
    :type project:          structures.project.Project
    :type section:          structures.project_section.ProjectSection
    :type step:             structures.project_step.ProjectStep
    :type shell_processing: ShellProcessing
    :type indices:          list[str]
    """
    logger.debug('processing shell script in step %s', step.name)
    format_args = project.global_args

    if vars is None:
        vars = dict()

    # here we try to determine how many cpus we want to use in this step
    # based on a cpu-prop value
    if step.parallel and step.parallel.prop:
        cpu_prop_conf = configure_string(step.parallel.prop, vars)
        cpu_prop = parse_cpu_property(cpu_prop_conf)
        vars.update(dict(__cpu__=cpu_prop))

    format_args = merge_dict(
        format_args,
        vars,
    )

    if step.shell:
        # determine tmp dir which will hold all the scripts
        tmp_dir_lst = [
            project.tmp_workdir,
            section.ord_name,
            step.ord_name,
        ]

        # if vars are given, we go deeper and create subdirectory for each configuration
        if indices:
            tmp_dir_lst += indices

        # convert list to file path string
        tmp_dir = os.path.join(*tmp_dir_lst)

        # create dir
        os.makedirs(tmp_dir, exist_ok=True)

        # the main script which will be executed, either using bash or with the help of a container
        tmp_sh = TempFile(os.path.join(tmp_dir, 'shell.sh'), verbose=step.verbose)

        # ---------------------------------------------------------------------

        with tmp_sh:
            tmp_sh.write_shebang()

            if vars:
                try:
                    vars_json = yaml.dump(vars, default_flow_style=False)
                except:
                    vars_json = str(vars)

                tmp_sh.write_section('CONFIGURATION', '\n'.join(['# ' + x for x in vars_json.splitlines()]))

            with shell_processing.init(tmp_sh):
                if project.init_shell:
                    configured = configure_string(project.init_shell, format_args)
                    tmp_sh.write_section('INIT SHELL', configured)

            with shell_processing.shell(tmp_sh):
                configured = configure_string(step.shell, format_args)
                tmp_sh.write_section('STEP SHELL', configured)

        # ---------------------------------------------------------------------

        format_args = merge_dict(
            project.global_args,
            vars,
        )

        crate = ProcessConfigCrate(
            args=['/bin/bash', tmp_sh.path],
            output=step.output,
            container=step.container,
            name=step.name if not indices else step.name + '(' + ' '.join(indices) + ')',
            collect=[project, step, None, format_args],
            vars=format_args
        )

        if not step.collect:
            crate.collect = []

        if not step.container:
            logger.debug('preparing vanilla shell script %s', tmp_sh.path)
            return crate
        else:
            tmp_cont = TempFile(os.path.join(tmp_dir, 'cont.sh'), verbose=step.verbose)
            with tmp_cont:
                tmp_cont.write_shebang()
                tmp_cont.write(configure_string(step.container.exec % tmp_sh.path, format_args))

            logger.debug('preparing container shell script %s', tmp_cont.path)
            crate.args = ['/bin/bash', tmp_cont.path]
            return crate


class ProcessConfigCrate(object):
    """
    :type args: list[str]
    :type output: str
    :type name: str
    :type collect: str
    :type vars: dict
    :type container: cihpc.core.structures.project_step_container.ProjectStepContainer
    """

    def __init__(self, args, output, container, name=None, collect=None, vars=None):
        self.args = args
        self.output = output
        self.container = container
        self.name = name or str(args)
        self.collect = collect
        self.vars = vars

    def __repr__(self):
        return 'Crate<{self.name}>'.format(self=self)


def process_popen(worker):
    """
    :type worker: multiproc.thread_pool.Worker
    :return:
    """
    crate = worker.crate
    io = DynamicIO(crate.output)
    result = ProcessStepResult()
    with io as fp:
        process = sp.Popen(crate.args, stdout=fp, stderr=sp.STDOUT)

        result.process = process
        with result:
            result.returncode = process.wait()
            if result.returncode == 0:
                logger.debug('ok [%d] ended with %d' % (process.pid, result.returncode))
            else:
                logger.warn('process [%d] ended with %d' % (process.pid, result.returncode))

    # try to grab output
    result.output = getattr(io.opener, 'output', None)
    return result
