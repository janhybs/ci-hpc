#!/usr/bin/python
# -*- coding: utf-8 -*-
# author: Jan Hybs
from collections import defaultdict

from pymongo import MongoClient

from utils import strings
from utils.config import Config as cfg
from utils.logging import logger

from defaults import artifacts_default_configuration, aggregation_default_configuration


class Fields(object):
    GIT_DATETIME = 'git-datetime'
    TEST_SIZE = 'test-size'
    GIT_TIMESTAMP = 'git-timestamp'
    UUID = 'uuid'
    ID = '_id'
    GIT_COMMIT = 'git-commit'
    DURATION = 'duration'


class Mongo(object):
    """
    Class Mongo manages connection and queries

    :type client          : MongoClient
    """

    SECTION_DATABASE = 'database'

    def __init__(self, project_name):

        self.project_name = project_name
        self._was_warned = defaultdict(lambda: False)

        opts = self._get_database(opts=None)
        opts['connect'] = True
        if 'type' in opts:
            opts.pop('type')

        logger.debug('establishing connection to the database')
        self.client = MongoClient(**opts)

        logger.debug('Connection established %s', str(self.client))
        logger.info('Connected to the mongo server %s', str(self))

    def _warn_first_time(self, warning):
        result = self._was_warned.get(warning) is False
        self._was_warned[warning] = True
        return result

    def _get_database(self, opts=None):
        if opts:
            return opts

        opts = cfg.get('%s.database' % self.project_name)
        if not opts:
            logger.error(
                'No valid database configuration found for the project %s \n'
                'You *must* specify this in your secret.yaml, if you want to use \n'
                'database features.',
                self.project_name,
            )
            raise Exception('No database configuration found')
        return opts

    def __repr__(self):
        return 'Mongo({self.client.address[0]}:{self.client.address[1]})'.format(self=self)


class CIHPCMongo(Mongo):
    """
    A database class which handles connections and configuration loading

    Attributes
    ----------
    db : pymongo.database.Database
        Main database containing all the reports and file logs

    reports : pymongo.database.Collection
        A collection containing all the reports

    files : pymongo.database.Collection
        A collection containing all the file logs
    """

    _instances = dict()

    SECTION_ARTIFACTS = 'artifacts'
    SECTION_VISUALISATION = 'visualisation'

    def __init__(self, project_name):
        """
        Parameters
        ----------
        project_name : str
            name of the project
        """

        super(CIHPCMongo, self).__init__(project_name)

        opts = self._get_artifacts(opts=None)
        self.db = self.client.get_database(opts.get('db_name'))
        self.reports = self.db.get_collection(opts.get('col_timers_name'))
        self.files = self.db.get_collection(opts.get('col_files_name'))

        self._pipeline = self._get_visualisation()

    def _get_artifacts(self, opts=None):
        if opts:
            return opts

        opts = cfg.get('%s.artifacts' % self.project_name)
        if not opts:
            if self._warn_first_time(self.SECTION_ARTIFACTS):
                logger.warning(
                    'No valid artifact configuration found for the project %s \n'
                    'It is recommended to specify this configuration in secret.yaml, \n'
                    'it can be as simple as this: \n'
                    '\n%s\n ',
                    self.project_name,
                    strings.to_yaml(
                        {self.project_name: {'artifacts': artifacts_default_configuration(self.project_name)}}
                    ), skip_format=True
                )

            opts = artifacts_default_configuration(self.project_name)
        return opts

    def _get_visualisation(self, opts=None):
        if opts:
            return opts

        opts = cfg.get('%s.visualisation' % self.project_name)
        if not opts:
            if self._warn_first_time(self.SECTION_VISUALISATION):
                logger.warning(
                    'No valid aggregation configuration found for the project %s. \n'
                    'Using default aggregation configuration \n'
                    'which may not suite this project... \n'
                    'It is recommended to specify this configuration in secret.yaml, \n'
                    'it can be as simple as this: \n'
                    '\n%s\n ',
                    self.project_name,
                    strings.to_yaml(
                        {self.project_name: {'visualisation': aggregation_default_configuration(self.project_name)}}
                    ), skip_format=True
                )

            opts = aggregation_default_configuration(self.project_name)
        return opts

    @property
    def pipeline(self):
        return self._pipeline.copy()

    def aggregate(self, pipeline):
        logger.debug('db.getCollection("%s").aggregate(\n%s\n)',
                     str(self.reports.name),
                     strings.pad_lines(strings.to_json(pipeline))
        )
        return self.reports.aggregate(pipeline)

    def find_one(self, filter, *args, **kwargs):
        logger.debug('db.getCollection("%s").findOne(\n%s\n)',
                     str(self.reports.name),
                     strings.pad_lines(strings.to_json(filter))
        )
        return self.reports.find_one(filter, *args, **kwargs)

    def agg(self, match=None, unwind=None, project=None, *args):
        """
        Shortcut for a aggregate method
        Parameters
        ----------
        match : dict
            $match aggregation object according to MongoDB specification
        unwind : dict or str
            $unwind aggregation object according to MongoDB specification
        project : dict
            $project aggregation object according to MongoDB specification
        """

        pipeline = list()

        if match:
            pipeline.append({'$match': match})

        if unwind:
            pipeline.append({'$unwind': unwind})

        if project:
            pipeline.append({'$project': project})

        if args:
            pipeline.extend(args)

        return self.aggregate(pipeline)

    @classmethod
    def get(cls, project_name):
        """
        Parameters
        ----------
        project_name : str
            name of the project

        Returns
        -------
        artifacts.db.mongo.CIHPCMongo
            instance of CIHPCMongo
        """

        if project_name not in cls._instances:
            cls._instances[project_name] = CIHPCMongo(project_name)

        return cls._instances[project_name]

