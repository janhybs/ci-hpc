#!/usr/bin/python
# author: Jan Hybs

import logging


logger = logging.getLogger(__name__)

import re
import os
import json
import hashlib
import shutil
from cihpc.common.utils.datautils import recursive_get
from cihpc.cfg.cfgutil import configure_object, configure_string


class ProcessStepCache(object):
    _arg_map = {
        'arg.branch': 'b',
        'arg.commit': 'c',
        'project-name': '-',
    }

    def __init__(self, step_cache, global_args=None, cwd='.'):
        """
        Function will clone given git
        and will checkout to a given branch and commit
        :type step_cache: cihpc.core.structures.project_step_cache.ProjectStepCache
        """
        self.global_args = global_args
        self.step_cache = step_cache
        self._cache_hash = None
        self._cache_name = None
        self.value = None
        self.cwd = os.path.abspath(cwd)

        self.storage = configure_string(
            self.step_cache.storage,
            self.global_args
        )
        self.directories = configure_object(
            self.step_cache.directories,
            self.global_args
        )

        self.fields = self.step_cache.fields or (
            'arg.branch', 'arg.commit', 'project-name'
        )

        value = self._compute_hash()
        self._cache_hash = hashlib.md5(value.encode()).hexdigest()
        self._cache_name = re.sub('[^a-zA-Z0-9._=,:-]', '', value)
        self.value = '%s-%s' % (self._cache_name, self._cache_hash)
        self.location = os.path.join(self.storage, self.value)

    def _compute_hash(self):
        hash_dict = dict()
        for f in self.fields:
            recursive_value = recursive_get(self.global_args, f)
            if recursive_value:
                hash_dict[self._arg_map.get(f, f)] = recursive_value

        return json.dumps(hash_dict, sort_keys=True, separators=(',', '-'))

    def exists(self):
        if os.path.exists(self.location) and os.path.isdir(self.location):
            return True
        return False

    def restore(self):
        for dirname in self.directories:
            from_dir = os.path.join(self.location, dirname)
            to_dir = os.path.join(self.cwd, dirname)
            logger.debug('restoring cache dir %s' % dirname)

            if os.path.exists(to_dir):
                logger.debug('rm tree %s' % to_dir)
                shutil.rmtree(to_dir)
            shutil.copytree(from_dir, to_dir)

    def save(self):
        for dirname in self.directories:
            from_dir = os.path.join(self.cwd, dirname)
            to_dir = os.path.join(self.location, dirname)
            logger.debug('saving cache dir %s' % dirname)

            if os.path.exists(to_dir):
                logger.debug('rm tree %s' % to_dir)
                shutil.rmtree(to_dir)
            shutil.copytree(from_dir, to_dir)

    def __repr__(self):
        return 'ProcessStepCache(%s, %s)' % (self._cache_hash, self._cache_name)


def _smart_hash(d):
    if not d:
        return tuple()

    result = list()
    if isinstance(d, dict):
        for k in sorted(list(d.keys())):
            v = '%s:%s' % (k, _smart_hash(d[k]))
            result.append(v)
    elif isinstance(d, list):
        for v in d:
            result.append(_smart_hash(v))
    else:
        return str(d)
    return ','.join([str(x) for x in result])
