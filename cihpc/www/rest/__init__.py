#!/bin/python3
# author: Jan Hybs


from flask_restful import Resource

from cihpc.common.utils import strings
from cihpc.common.logging import logger
from cihpc.common.utils import datautils as du


class ConfigurableView(Resource):
    def __init__(self):
        super(ConfigurableView, self).__init__()

    @classmethod
    def _process_list_args(cls, value):
        result: dict = dict([tuple(v.split('=')) for v in value])
        for k, v in result.items():
            if v.lower() == 'true':
                result[k] = True
            elif v.lower() == 'false':
                result[k] = False
            else:
                try:
                    result[k] = int(v)
                except:
                    result[k] = v
        return result

    @classmethod
    def error_empty_df(cls, filters):
        logger.info('empty result')
        return cls.show_error(
            status=300,
            message='No results found',
            description='\n'.join([
                '<p>This usually means provided filters filtered out everything.</p>',
                '<p>DEBUG: The following filters were applied:</p>',
                '<pre><code>%s</code></pre>' % strings.to_json(filters)

            ])
        )

    @classmethod
    def show_error(cls, message, status=400, description=''):
        logger.info('error [%d] %s' % (status, message))
        return dict(
            status=status,
            message=message,
            description=description
        )

    @classmethod
    def group_by(cls, df, groupby):
        """
        :rtype: list[(list[str], list[str], list[str], pd.DataFrame)]
        """
        if not groupby:
            yield ('', '', '', df)
        else:

            keys = du.ensure_iterable(list(groupby.keys()))
            names = du.ensure_iterable(list(groupby.values()))

            for group_values, group_data in df.groupby(keys):
                yield (
                    du.ensure_iterable(group_values), du.ensure_iterable(keys), du.ensure_iterable(names), group_data)
