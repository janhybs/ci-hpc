#!/usr/bin/python
# author: Jan Hybs


import itertools
import shutil
from utils.logging import logger

import os

from structures.project_step import ProjectStep
from structures.project_section import ProjectSection
from structures.project import Project

from proc import merge_dict, iter_over
from proc.step.step_git import process_step_git
from proc.step.step_shell import process_step_shell, ShellProcessing
from proc.step.step_collect import process_step_collect
from proc.step.step_measure import process_step_measure


class ProcessProject(object):
    """
    :type project:  Project
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
        logger.info('processing project %s', self.project.name)
        # remove old configuration
        shutil.rmtree('tmp.%s' % self.project.name, True)

        # process both sections
        for section in [self.project.install, self.project.test]:
            with logger:
                self.process_section(section)

    def process_section(self, section):
        """
        Method will process every step in a section
        :type section:  ProjectSection
        """
        logger.info('processing section %s', section.name)

        for step in section:
            with logger:
                for i in range(step.repeat):
                    logger.debug('Repetition %02d of %02d', i + 1, step.repeat)
                    self.process_step(step, section)

    def process_step_with_vars(self, step, section, vars):
        """
        Method will actually process given step with a given configuration
        Everything else happening before was for this moment

        :type step:     ProjectStep
        :type section:  ProjectSection
        """
        if not step.shell:
            logger.debug('no shell defined in step %s', step.name)
        else:
            shell_processing = ShellProcessing()
            if step.measure:
                process_step_measure(step, step.measure, shell_processing)

            process_step_shell(self.project, section, step, vars, shell_processing)

    def process_step(self, step, section):
        """
        :type step:     ProjectStep
        :type section:  ProjectSection
        """

        def extract_first(iterator):
            return next(iter(iterator))

        def ensure_list(o):
            if isinstance(o, list):
                return o
            return [o]

        if not step.enabled:
            logger.debug('step %s is disabled', step.name)
            return
        logger.info('processing step %s', step.name)

        if not step.git:
            logger.debug('no repos setup')
        else:
            process_step_git(step.git, self.project.global_args)

        if step.variables:
            logger.debug('found %d build matrices', len(step.variables))
            logger.debug('processing step %s with build matrix', step.name)
            with logger:
                for matrix in step.variables:
                    variables = extract_first(matrix.values())
                    values = [ensure_list(extract_first(y.values())) for y in variables]
                    names = [extract_first(y.keys()) for y in variables]
                    product = list(dict(zip(names, x)) for x in itertools.product(*values))
                    logger.debug('created build matrix with %d configurations', len(product))

                    for vars, current, total in iter_over(product):
                        with logger:
                            vars = merge_dict(vars, dict(__total__=total, __current__=current+1))
                            self.process_step_with_vars(step, section, vars)

                            # artifact collection
                            if step.collect:
                                format_args = merge_dict(
                                    self.project.global_args,
                                    vars,
                                )
                                process_step_collect(step, format_args)
        else:
            logger.info('processing step %s without variables', step.name)
            self.process_step_with_vars(step, section, None)

    @classmethod
    def configure(cls, o, d):
        for k in o:
            if type(o[k]) is str:
                o[k] = o[k].format(**d)
            elif type(o[k]) is dict:
                o[k] = cls.configure(o[k], d)
        return o

# argparseimport argparse
# parser = argparse.ArgumentParser()
# parser.add_argument('-b', '--branch', action='append', type=lambda kv: tuple(kv.split(":")), default=[])
# parser.add_argument('-c', '--commit', action='append', type=lambda kv: tuple(kv.split(":")), default=[])
# args = parser.parse_args()
#
#
# global_args = dict(
#     args=dict(
#         branch=defaultdict(lambda: 'master', **dict(args.branch)),
#         commit=defaultdict(lambda: '', **dict(args.commit)),
#     )
# )
# with open('config.yaml') as fp:
#     config = yaml.load(fp)
#
# flow123d = Project('flow123d', **config['flow123d'])
# flow123d.global_args.update(global_args)
# pp = ProcessProject(flow123d)
# pp.process()
