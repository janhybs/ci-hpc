#!/usr/bin/python3
# author: Jan Hybs

import base64
import json
import logging

from flask_restful import Resource

from cihpc.common.utils import strings
from cihpc.common.utils.timer import Timer
from cihpc.core.db import CIHPCMongo
from cihpc.www.cfg.project_config import ProjectConfig


logger = logging.getLogger(__name__)


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

        logger.info(strings.to_json(self.options))

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
