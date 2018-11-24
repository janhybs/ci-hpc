#!/usr/bin/python
# author: Jan Hybs

import os
import sys


__dir__ = os.path.abspath(os.path.dirname(__file__))
__root__ = os.path.dirname(os.path.dirname(__dir__))

__cfg__ = os.path.join(__root__, 'cfg')
__src__ = os.path.join(__root__, 'cihpc')


class global_configuration(object):
    """
    :type project_git: structures.project_step_git.ProjectStepGit
    """
    tty = getattr(sys.stdout, 'isatty', lambda: False)()
    root = __root__
    cfg = __cfg__
    src = __src__

    # path to the main.py
    main_py = os.path.join(__src__, 'main.py')

    # default location for the log file abd the format
    log_path = os.path.join(__root__, '.ci-hpc.log')
    log_style = 'short'

    # default cache is for 10 entries or 10 minutes
    cache_type = 'TTLCache'  # or LRUCache or None
    cache_opts = dict(
        maxsize=10,
        ttl=10 * 60
    )

    # this file should be PROTECTED, as it may contain passwords and database connection details
    cfg_secret_path = os.path.join(__cfg__, 'secret.yaml')

    # project details
    project_name = None
    project_cfg = None
    project_cfg_dir = '.'

    # clear tmp files if True
    project_clear_temp = False

    # path to a main repository, from which
    # git information is taken
    project_git = None
