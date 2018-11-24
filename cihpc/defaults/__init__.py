#!/bin/python3
# author: Jan Hybs


def aggregation_default_configuration(project_name=None):
    """
    Method returns default aggregation configuration for the given project

    If no project name is given, will use
    value 'default' instead.

    Parameters
    ----------
    project_name : str
        name of the project
    """
    if not project_name:
        project_name = 'default'

    return [
        {
            '$unwind': '$libs',
        },
        {
            '$unwind': '$timers',
        }
    ]


def artifacts_default_configuration(project_name=None):
    """
    Method returns default artifact configuration for the given project

    If no project name is given, will use
    value 'default' instead.

    Parameters
    ----------
    project_name : str
        name of the project
    """
    if not project_name:
        project_name = 'default'

    return dict(
        db_name=project_name,
        col_timers_name='timers',
        col_files_name='files',
        col_history_name='hist',
    )
