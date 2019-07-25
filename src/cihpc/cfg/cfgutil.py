#!/usr/bin/python
# author: Jan Hybs

import itertools
from loguru import logger
import os
import re
from copy import deepcopy, copy

import yaml




_configure_object_regex = re.compile('<([a-zA-Z0-9_$.-]+)(\|[a-zA-Z_0-9]+)?>')
_configure_object_dict = {
    's':str,
    'i':int,
    'f':float,
    'b':bool,

    '0':lambda x: str(x).split('_')[0],
    '1':lambda x: str(x).split('_')[1],
    '2':lambda x: str(x).split('_')[2],
    '3':lambda x: str(x).split('_')[3],

    '0i':lambda x: int(str(x).split('_')[0]),
    '1i':lambda x: int(str(x).split('_')[1]),
    '2i':lambda x: int(str(x).split('_')[2]),
    '3i':lambda x: int(str(x).split('_')[3]),
}
_no_such_value = object()


class Config(object):
    """
    Class which loads a .config.yaml file which should be located somewhere in a parent directory
    """
    _instance = None
    _hostname = None
    _cfg = dict()

    @classmethod
    def get(cls, *args, **kwargs):
        if not cls._instance:
            from cihpc.cfg.config import global_configuration

            cls.init(global_configuration.cfg_secret_path)

        return cls._instance._get(*args, **kwargs)

    @classmethod
    def hostname(cls):
        if not cls._hostname:
            import platform

            cls._hostname = platform.node()
            logger.debug(f'determined hostname as "{cls._hostname}"')
        return cls._hostname

    @classmethod
    def init(cls, config_location=None):
        if cls._instance:
            return cls._instance

        if config_location is None:
            current = 0
            max_limit = 10
            root = os.path.dirname(__file__)

            config_file = os.path.join(root, 'secret.yaml')
            while current < max_limit:
                config_file = os.path.join(root, 'secret.yaml')
                current += 1
                if os.path.exists(config_file):
                    break
                root = os.path.dirname(root)
        else:
            config_file = config_location

        cls._instance = Config()
        try:
            with open(config_file, 'r') as fp:
                cls._cfg = yaml_load(fp.read()) or dict()
        except Exception as e:
            logger.exception(f'Failed to load/parse {config_file} configuration file, will use empty dict')
            logger.warning(f'You may want to create this file in order to use database connection')
            cls._cfg = dict()
        return cls._instance

    def _get(self, key=None, default=None):
        """
        :rtype: dict or list or string or int or bool
        """
        self.__class__.init()
        cfg_copy = deepcopy(self.__class__._cfg)
        if key is None:
            return cfg_copy

        keys = str(key).split('.')
        if len(keys) == 1:
            return cfg_copy.get(key, default)

        r = cfg_copy
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
        try:
            cfg['pymongo']['password'] = '---HIDDEN---'
        except:
            pass
        return yaml.dump(cfg, indent=4)


def yaml_load(s):
    return yaml.safe_load(s)


def read_file(path, default=''):
    if os.path.exists(path):
        with open(path, 'r') as fp:
            return fp.read()
    else:
        return default


def load_config(path, replace=True, hostname_conditions=True, hostname=None):
    if not hostname_conditions:
        return yaml_load(read_file(path, default='{}'))
    obj = yaml_load(read_file(path, default='{}'))

    # grab hostname
    host = hostname or Config.hostname()

    result = dict()
    simple_ones = {k: v for k, v in obj.items() if not isinstance(v, dict)}
    complex_ones = {k: v for k, v in obj.items() if isinstance(v, dict)}

    # add simple variables
    result.update(simple_ones)

    for k, other_dict in complex_ones.items():
        regex = k.replace('.', '\\.').replace('*', '.*')

        # we found our hostname match
        if re.match(regex, host):
            logger.debug(f'setting conditional variables (hostname {host} matches definition {k})')
            result.update(other_dict)
            return result
    return result


def configure_file(path, variables, convert=yaml_load, start='<', stop='>'):
    content = yaml.dump(yaml_load(read_file(path)))
    iterable_keys = list()
    iterable_vals = list()
    rest = dict()

    for k, v in variables.items():
        if isinstance(v, list):
            iterable_keys.append(k)
            iterable_vals.append(v)
        else:
            rest[k] = v

    for g in itertools.product(*iterable_vals):
        single_config = rest.copy()
        single_config.update(dict(zip(iterable_keys, g)))

        # for k, v in single_config.items():
        #     single_content = single_content.replace('%s%s%s' % (start, k, stop), str(v))
        yield configure_object(
            convert(content),
            single_config,
            preserve_if_missing=True
        )


def configure_object(obj, vars, preserve_if_missing=False):
    """
    Configure given object (replaces placeholders <KEY> with VALUE contained in a given vars)
        by default, everything is converted to string, to change conversion type use syntax:
        <KEY|i> to convert value to int
        <KEY|f> to convert value to float
        <KEY|s> to convert value to string (default)
    :type obj: dict or list
    :type vars: dict
    """
    if not vars:
        return obj

    if obj is None:
        return None

    if isinstance(obj, list):
        obj_copy = deepcopy(obj)
        for i, v in enumerate(obj_copy):
            obj_copy[i] = configure_object(v, vars, preserve_if_missing)
        return obj_copy

    if isinstance(obj, dict):
        obj_copy = deepcopy(obj)
        for k, v in obj_copy.items():
            obj_copy[k] = configure_object(v, vars, preserve_if_missing)
        return obj_copy

    else:
        return configure_string(obj, vars, preserve_if_missing)


_warn_cache = dict()
def _get_property(obj, val, default=_no_such_value):
    """
    :type val: str
    :type obj: dict
    """
    root = obj
    for k in val.split('.'):
        try:
            if isinstance(root, dict):
                root = root[k]
            else:
                root = getattr(root, k)
        except:
            key = str(val), id(obj)
            if key not in _warn_cache:
                # logger.debug(f'could not find propery {val} on {obj')
                _warn_cache[key] = True
            return default
    return root


def configure_string(value, vars, preserve_if_missing=False):
    matches = _configure_object_regex.findall(str(value))
    if matches:
        value = str(value)
        for key, dtype in matches:
            orig = '<%s%s>' % (key, dtype)
            func = _configure_object_dict.get(dtype[1:], str)
            prop = _get_property(vars, key)

            # if no such value exists
            if prop is _no_such_value:
                # if we want to preserve the value, simply skip sub
                if preserve_if_missing:
                    continue
                # otherwise we return default class instance such as int() i.e. 0 or float() i.e. 0.0
                else:
                    value = func()
                    continue

            # value exists, we try to return it
            else:
                val = str(value).replace(orig, str(prop))
                try:
                    value = func(val)
                except:
                    value = func()
    return value


def find_valid_configuration(*hints, file, raise_if_not_found=False):
    for hint in hints:
        if hint and os.path.isdir(hint) and os.path.isfile(os.path.join(hint, file)):
            return hint

    if raise_if_not_found:
        error_msg = [
            f'no valid configuration (file {file}) found '
            'in any of the following paths'
        ]
        for i, hint in enumerate(hints):
            error_msg += ['%d) %s' % (i, str(hint))]

        logger.error('\n'.join(error_msg))
    return None
