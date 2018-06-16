import os
import subprocess as sp

from files.temp_file import TempFile
from proc import merge_dict
from utils.logging import logger


def process_step_shell(project, section, step, vars):
    """
    Function will execute shell from given step using specific vars in the process
    :type project:        structures.project.Project
    :type section:        structures.project_section.ProjectSection
    :type step:           structures.project_step.ProjectStep
    """
    logger.info('processing shell script in step %s', step.name)
    format_args = project.global_args.copy()
    if vars:
        format_args = merge_dict(
            format_args,
            vars
        )

    if step.shell:
        # determine tmp dir which will hold all the scripts
        tmp_dir = os.path.join(
            'tmp.%s' % project.name,
            section.ord_name,
            '%d.%s' % (section.index(step) + 1, step.name))

        # if vars are given, we go deeper and create subdirectory for each configuration
        if vars:
            tmp_dir = os.path.join(
                tmp_dir,
                '%d.%d.conf' % (format_args['__current__'], format_args['__total__']))

        # create dir
        os.makedirs(tmp_dir, exist_ok=True)

        # the main script which will be executed, either using bash or with the help of a container
        tmp_sh = TempFile(os.path.join(tmp_dir, 'shell.sh'), verbose=step.verbose)

        with tmp_sh:
            tmp_sh.write_shebang()
            if project.init_shell:
                tmp_sh.write('# INIT SHELL PART START')
                tmp_sh.write(project.init_shell.format(**format_args))
                tmp_sh.write('# INIT SHELL PART END\n')
            tmp_sh.write(step.shell.format(**format_args))

        if not step.container:
            logger.info('running vanilla shell script %s', tmp_sh.path)
            sp.Popen(['/bin/bash', tmp_sh.path]).wait()
        else:
            tmp_cont = TempFile(os.path.join(tmp_dir, 'cont.sh'), verbose=step.verbose)

            with tmp_cont:
                tmp_cont.write_shebang()
                if step.container.load:
                    tmp_cont.write(step.container.load.format(**format_args))
                tmp_cont.write((step.container.exec % tmp_sh.path).format(**format_args))

            logger.info('running container shell script %s', tmp_cont.path)
            sp.Popen(['/bin/bash', tmp_cont.path]).wait()