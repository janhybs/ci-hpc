#!/usr/bin/python
# -*- coding: utf-8 -*-
# author: Jan Hybs

from pymongo import MongoClient
from utils.config import Config as cfg
from utils.logging import logger



class Fields(object):
    GIT_DATETIME = 'git-datetime'
    TEST_SIZE = 'test-size'
    GIT_TIMESTAMP = 'git-timestamp'
    UUID = 'uuid'
    GIT_COMMIT = 'git-commit'
    DURATION = 'duration'


class Mongo(object):
    """
    Class Mongo manages connection and queries

    :type client          : MongoClient
    """

    def __init__(self):
        kwargs = cfg.get('pymongo')
        kwargs['connect'] = True

        logger.info('establishing connection to the database')
        self.client = MongoClient(**kwargs)
        logger.debug('Connection established %s', str(self.client))

    def auth(self, username=None, password=None):
        logger.debug('authenticating...')
        return self.client.admin.authenticate(username, password)

    def __repr__(self):
        return 'DB({self.client.address[0]}:{self.client.address[1]})'.format(self=self)


class CIHPCMongo(Mongo):
    """
    Attributes
    ----------
    db : pymongo.database.Database
        Main database containing all the reports and file logs

    reports : pymongo.database.Collection
        A collection containing all the reports

    files : pymongo.database.Collection
        A collection containing all the file logs
    """
    def __init__(self, opts):
        """
        Parameters
        ----------
        opts : dict
            Configuration with database name and collection names
        """
        super(CIHPCMongo, self).__init__()

        self.db = self.client.get_database(opts.get('dbname'))
        self.reports = self.db.get_collection(opts.get('reports_col'))
        self.files = self.db.get_collection(opts.get('files_col'))

    def aggregate(self, pipeline):
        return self.reports.aggregate(pipeline)

    def agg(self, match=None, unwind=None, project=None, *args):
        """
        Parameters
        ----------
        match : dict
            $match aggregation object according to MongoDB specification
        unwind : dict or str
            $unwind aggregation object according to MongoDB specification
        project : dict
            $project aggregation object according to MongoDB specification
        """
        result = list()

        if match:
            result.append({'$match': match})

        if unwind:
            result.append({'$unwind': unwind})

        if project:
            result.append({'$project': project})

        if args:
            result.extend(args)