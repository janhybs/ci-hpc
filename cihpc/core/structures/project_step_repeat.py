#!/usr/bin/python
# author: Jan Hybs

import logging

from cihpc.common.utils.datautils import recursive_get


logger = logging.getLogger(__name__)


class ProjectStepRepeat(object):
    """
    A class which holds information about repetition value for a ProjectStep
    :type fixed_value: int
    :type dynamic_value: int
    """

    def __init__(self, kwargs):

        if kwargs is None:
            self.fixed_value = 1
            self.dynamic_value = None

        elif type(kwargs) is int:
            self.fixed_value = kwargs
            self.dynamic_value = None

        elif isinstance(kwargs, dict):
            self.dynamic_value = kwargs.get('no-less-than', None)
            self.fixed_value = kwargs.get('exactly', self.dynamic_value)

            if self.dynamic_value is None and self.fixed_value is None:
                raise ValueError('Specify either "exactly" and/or "no-less-than" values')

        else:
            raise ValueError('kwargs must be int or dictionary')

        self._connection = None
        self._remains = None

    def load_stats(self, project_name, step_name, git_commit=None):
        if not self.is_complex():
            raise NotImplementedError('no point to load db stats on with fixed repetition value')

        if not self._connection:
            from cihpc.core.db import CIHPCMongo

            self._connection = CIHPCMongo.get(project_name)

        filters = dict(name=step_name)
        if git_commit:
            filters['git.commit'] = git_commit
        items = self._connection.commit_history(filters)

        if not items:
            if git_commit:
                logger.info('no history for the step %s and the commit %s\n'
                            'will run %d repetitions' % (step_name, git_commit, self.dynamic_value))
            else:
                logger.info('no history for the step %s\n'
                            'will run %d repetitions' % (step_name, self.dynamic_value))

            # return the minimum values specified
            return self.dynamic_value

        total = 0
        duration = 0
        for item in items:
            reps = recursive_get(item, 'reps', 0)
            dura = recursive_get(item, 'duration', 0.0)
            date = recursive_get(item, 'git.datetime', '?')

            total += reps
            duration += dura

            logger.debug('found %d reps from %s which took %1.3fsec' % (reps, date, dura))

        self._remains = self.dynamic_value - total

        if self._remains > 0:
            estimated_duration = ''
            if total > 0 and duration > 0:
                duration_per_repetition = duration / total
                duration_total = duration_per_repetition * self._remains
                # TODO ugly code
                estimated_duration = '\nestimated duration is %d secs (ie. %1.1f mins or %1.2f hours)' % (
                    int(duration_total), float(duration_total / 60), float(duration_total / 3600)
                )
            logger.info('found total of %d results\n'
                        'need to run %d more repetitions%s', total, self._remains, estimated_duration)
        elif self._remains < 0:
            logger.info('found total of %d results\n'
                        'no need to run any more repetitions (they are %d extra)', total, total - self._remains)
        else:
            logger.info('found total of %d results\n'
                        'no need to run any more repetitions', total)

        # 0 is the minimum value we want
        self._remains = max(self._remains, 0)

    @property
    def value(self):
        if self.is_complex():
            if self._remains is not None:
                return self._remains
            return self.dynamic_value
        return self.fixed_value

    def is_complex(self):
        return self.dynamic_value is not None
