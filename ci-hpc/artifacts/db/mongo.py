#!/usr/bin/python
# -*- coding: utf-8 -*-
# author: Jan Hybs

from pymongo import MongoClient
from utils.config import Config as cfg
from utils.logging import logger


class Mongo(object):
    """
    Class Mongo manages connection and queries
    :type client          : MongoClient
    """

    def __init__(self, auto_auth=True):
        kwargs = cfg.get('pymongo')
        username = kwargs.pop('username')
        password = kwargs.pop('password')
        logger.info('establishing connection to the database')
        self.client = MongoClient(**kwargs)
        self.needs_auth = True

        if auto_auth and self.needs_auth:
            self.auth(username, password)
            self.needs_auth = False

        logger.debug('Connection established %s', str(self.client))

    def auth(self, username=None, password=None):
        logger.debug('authenticating...')
        return self.client.admin.authenticate(username, password)

    def __repr__(self):
        return 'DB({self.client.address[0]}:{self.client.address[1]})'.format(self=self)
