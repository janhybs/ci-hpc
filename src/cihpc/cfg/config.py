#!/usr/bin/python
# author: Jan Hybs

import os
import sys
import pathlib


__root__ = str(pathlib.Path(__file__).parent.parent.parent.parent)
__cfg__ = os.path.join(__root__, 'cfg')


__cwd__ = os.getcwd()
__home__ = os.environ.get('CIHPC_HOME', None) or os.environ.get('CIHPC_ROOT', None) or __cwd__
__src__ = os.path.join(__root__, 'src')
__tmp__ = os.path.join(__root__, '.tmp')


__main_py__ = sys.argv[0]
__secret_yaml__ = os.environ.get('CIHPC_SECRET', None) or os.path.join(__cfg__, 'secret.yaml')


class global_configuration(object):
    """
    :type project_git: cihpc.structures.project_step_git.ProjectStepGit
    """
    tty = getattr(sys.stdout, 'isatty', lambda: False)()
    root = __root__
    src = __src__
    cwd = __cwd__
    home = __home__

    # path to the main.py
    main_py = __main_py__
    exec_args = [sys.executable, __main_py__]

    # default cache is for 10 entries or 10 minutes
    cache_type = 'TTLCache'  # or LRUCache or None
    cache_opts = dict(
        maxsize=10,
        ttl=10 * 60
    )

    # this file should be PROTECTED, as it may contain passwords and database connection details
    cfg_secret_path = __secret_yaml__

    # project details
    project_name = None
    project_cfg = None
    project_cfg_dir = '.'

    # clear tmp files if True
    project_clear_temp = False

    # path to a main repository, from which
    # git information is taken
    project_git = None
