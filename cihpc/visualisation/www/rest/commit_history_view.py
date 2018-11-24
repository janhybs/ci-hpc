#!/usr/bin/python3
# author: Jan Hybs

from cihpc.visualisation.cfg.project_config import ProjectConfig

import json
import base64

from cihpc.utils import strings
from flask_restful import Resource
from cihpc.artifacts.db.mongo import CIHPCMongo
from cihpc.utils.logging import logger
from cihpc.utils.timer import Timer


class CommitHistoryView(Resource):

    def __init__(self):
        super(CommitHistoryView, self).__init__()
        self.options = dict()
        self.config = None  # type: ProjectConfig
        self.mongo = None  # type: CIHPCMongo

    def prepare(self, project, base64data=None):
        if base64data:
            self.options = json.loads(
                base64.decodebytes(base64data.encode()).decode()
            )
        else:
            logger.warning('no options given')
            self.options = dict()

        logger.info(strings.to_json(self.options), skip_format=True)

        self.config = ProjectConfig.get(project)
        self.mongo = CIHPCMongo.get(project)

    @Timer.decorate('CommitHistory: get', logger.info)
    def get(self, project):
        self.prepare(project)
        items = self.mongo.commit_history()
        if not items:
            items = self.mongo.timers_stats()
            for item in items:
                item['variables'] = dict()
                item['config'] = None
        return items
