#!/usr/bin/python
# author: Jan Hybs

import os
import yaml
import utils.extend_yaml

from utils.logging import logger


class Config(object):
    """
    Class which loads a .config.yaml file which should be located somewhere in a parent directory
    """
    _instance = None
    _cfg = dict()

    @classmethod
    def get(cls, *args, **kwargs):
        return cls._instance._get(*args, **kwargs)

    @classmethod
    def init(cls, config_location=None):
        if cls._instance:
            return cls._instance

        if config_location is None:
            current = 0
            max_limit = 10
            root = os.path.dirname(__file__)

            config_file = os.path.join(root, '.config.yaml')
            while current < max_limit:
                config_file = os.path.join(root, '.config.yaml')
                current += 1
                if os.path.exists(config_file):
                    break
                root = os.path.dirname(root)
        else:
            config_file = config_location

        cls._instance = Config()
        try:
            cls._cfg = yaml.load(open(config_file, 'r').read()) or dict()
        except Exception as e:
            logger.warn_exception('Failed to load/parse %s configuration file, will use empty dict', config_file)
            cls._cfg = dict()
        return cls._instance

    def _get(self, key=None, default=None):
        """
        :rtype: dict or list or string or int or bool
        """
        self.__class__.init()
        if key is None:
            return self.__class__._cfg

        keys = str(key).split('.')
        if len(keys) == 1:
            return self.__class__._cfg.get(key, default)

        r = self.__class__._cfg
        for k in keys:
            r = r.get(k, {})
        return r

    def _set(self, key, value):
        """
        :rtype: dict or list or string or int or bool
        """
        self.__class__.init()
        self.__class__._cfg[key] = value
        return value

    def __getitem__(self, item):
        return self.get(item)

    def __repr__(self):
        cfg = self.__class__._cfg.copy()
        try:    cfg['pymongo']['password'] = '---HIDDEN---'
        except: pass
        return yaml.dump(cfg, indent=4)


def yaml_dump(obj, default_flow_style=False, width=120, **kwargs):
    return yaml.dump(obj, default_flow_style=default_flow_style, width=width, **kwargs)


def yaml_load(s):
    return yaml.load(s)


def read_file(path, default=''):
    if os.path.exists(path):
        with open(path, 'r') as fp:
            return fp.read()
    else:
        return default


def load_config(path, replace=True):
    return yaml_load(read_file(path, default='{}'))


def configure_file(path, variables, convert=yaml_load, start='<', stop='>'):
    content = read_file(path)
    for k, v in variables.items():
        content = content.replace('%s%s%s' % (start, k, stop), v)

    return convert(content)


utils.extend_yaml.extend()
