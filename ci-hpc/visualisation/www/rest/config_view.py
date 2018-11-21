#!/usr/bin/python3
# author: Jan Hybs

from flask_restful import Resource
from visualisation.cfg.project_config import ProjectConfig


class ConfigView(Resource):
    """
    a view which returns project configuration fro the given project name

    """

    def get(self, project):
        config = ProjectConfig.get(project)

        return config.cfg
