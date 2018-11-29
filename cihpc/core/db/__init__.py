#!/bin/python3
# author: Jan Hybs
import logging
from collections.__init__ import defaultdict

from pymongo import MongoClient

from cihpc.cfg.cfgutil import Config as cfg
from cihpc.common.utils import strings, datautils
from cihpc.common.utils.timer import Timer


logger = logging.getLogger(__name__)


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

        logger.debug('connection established %s', str(self.client))
        logger.info('connected to the mongo server %s', str(self))

    def _warn_first_time(self, warning):
        result = self._was_warned.get(warning) is False
        self._was_warned[warning] = True
        return result

    def _get_database(self, opts=None):
        if opts:
            return opts

        opts = cfg.get('%s.database' % self.project_name)
        if not opts:
            logger.warning(
                'No valid database configuration found for the project %s \n'
                'You *must* specify this in your secret.yaml, if you want to use \n'
                'database features.',
                self.project_name,
            )
            raise Exception('No database configuration found for %s' % self.project_name)
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
        self.history = self.db.get_collection(opts.get('col_history_name'))

    def _get_artifacts(self, opts=None):
        if opts:
            return opts

        base_opts = self.artifacts_default_configuration(self.project_name)
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
                        {self.project_name: {'artifacts': self.artifacts_default_configuration(self.project_name)}}
                    )
                )

            opts = self.artifacts_default_configuration(self.project_name)
        base_opts.update(opts)
        return base_opts

    def find_all(self, filter=None, projection=None, *args, flatten=True, **kwargs):
        if not filter:
            filter = dict()

        logger.info('db.getCollection("%s").find(\n'
                    '%s\n'
                    ',\n%s\n)',
                    str(self.reports.name),
                    strings.pad_lines(strings.to_json(filter)),
                    strings.pad_lines(strings.to_json(projection)),
                    )

        with Timer('db find: db-stuff', log=logger.debug):

            with Timer('db find: db-stuff: find', log=logger.debug):
                # TODO this may take a while depending on the size of the collection
                cursor = self.reports.find(filter, projection, *args, **kwargs)

            with Timer('db find: db-stuff: fetch and flatten', log=logger.debug):
                if flatten:
                    items = [datautils.flatten(x, sep='.') for x in list(cursor)]
                else:
                    items = list(cursor)

        return items

    def find_one(self, filter=None, *args, **kwargs):
        if not filter:
            filter = dict()

        logger.debug('db.getCollection("%s").findOne(\n%s\n)',
                     str(self.reports.name),
                     strings.pad_lines(strings.to_json(filter))
                     )
        return self.reports.find_one(filter, *args, **kwargs)

    def aggregate(self, match=None, unwind=None, project=None, flatten=True, *args):
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

        logger.debug('db.getCollection("%s").aggregate(\n%s\n)',
                     str(self.reports.name),
                     strings.pad_lines(strings.to_json(pipeline))
                     )

        with Timer('db find: db-stuff', log=logger.debug):

            with Timer('db aggregate: db-stuff: find', log=logger.debug):

                # TODO this may take a while depending on the size of the collection
                cursor = self.reports.aggregate(pipeline)

            with Timer('db aggregate: db-stuff: fetch and flatten', log=logger.debug):
                if flatten:
                    items = [datautils.flatten(x, sep='.') for x in list(cursor)]
                else:
                    items = list(cursor)

        return items

    def commit_history(self, filters=None, excludes=('config',)):
        exclude = {x: 0 for x in excludes} if excludes else None

        return list(self.history.find(filters, exclude))

    def timers_stats(self):
        pipeline = [
            {
                '$group': {
                    '_id'    : {
                        'hash': '$git.commit',
                        'date': {
                            '$dateToString': {
                                'date'  : '$git.datetime',
                                'format': '%Y-%m-%d %H:%M:%S'
                            }
                        }
                    },
                    'dur_sum': {'$sum': '$result.duration'},
                    'dur_avg': {'$avg': '$result.duration'},
                    'dur_max': {'$max': '$result.duration'},
                    'dur_min': {'$min': '$result.duration'},
                    'items'  : {'$sum': 1},
                }
            },
            {
                '$sort': {
                    '_id.date': -1
                }
            }
        ]
        logger.debug('db.getCollection("%s").aggregate(\n%s\n)',
                     str(self.reports.name),
                     strings.pad_lines(strings.to_json(pipeline))
                     )
        return list(self.reports.aggregate(pipeline))

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

    @staticmethod
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
