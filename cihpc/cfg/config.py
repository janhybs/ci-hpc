#!/usr/bin/python
# author: Jan Hybs

import os
import sys


__cwd__ = os.getcwd()
__home__ = os.environ.get('CIHPC_HOME', None) or os.environ.get('CIHPC_ROOT', None) or __cwd__
__dir__ = os.path.abspath(os.path.dirname(__file__))
__root__ = os.path.dirname(os.path.dirname(__dir__))

__cfg__ = os.path.join(__home__, 'cfg')
__src__ = os.path.join(__root__, 'cihpc')
__main_py__ = os.path.join(__root__, 'cihpc', '__init__.py')


class global_configuration(object):
    """
    :type project_git: cihpc.structures.project_step_git.ProjectStepGit
    """
    tty = getattr(sys.stdout, 'isatty', lambda: False)()
    root = __root__
    cfg = __cfg__
    src = __src__
    cwd = __cwd__

    # path to the main.py
    main_py = __main_py__

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

    @classmethod
    def update_cfg_path(cls, cfg):
        cls.cfg = cfg
        cls.cfg_secret_path = os.path.join(cfg, 'secret.yaml')
