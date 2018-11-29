#!/usr/bin/python
# author: Jan Hybs

import argparse
import datetime
import random
import json
import yaml

from cihpc.common.utils import dateutils as dateutils
from cihpc.common.utils import extend_yaml


extend_yaml.extend()


def generate_random_key(length=8):
    """
    :type length: int
    """
    return ''.join(random.choice('0123456789abcdef') for _ in range(length))


def pad_lines(string, pad=2):
    """
    :type pad: int or str
    :type string: str
    """
    pad_str = pad if isinstance(pad, str) else int(pad) * ' '
    return '\n'.join([pad_str + line for line in string.splitlines()])


def to_json(obj, **kwargs):
    kwargs.update(dict(
        cls=JSONEncoder,
        indent=4,
        sort_keys=True,
    ))
    return json.dumps(obj, **kwargs)


class JSONEncoder(json.JSONEncoder):

    def default(self, o):
        from bson import ObjectId
        import numpy as np
        import pandas as pd

        if isinstance(o, datetime.datetime):
            return dateutils.long_format(o)

        if isinstance(o, ObjectId):
            return str(o)

        if isinstance(o, np.ndarray):
            try:
                return list(np.around(o, 2))
            except Exception as e:
                return list(o)

        if isinstance(o, pd.Series):
            return list(o)
        if isinstance(o, pd.DataFrame):
            return o.values
            # return o.isoformat()

        if hasattr(o, 'to_json'):
            return o.to_json()

        return json.JSONEncoder.default(self, o)


def to_yaml(obj, default_flow_style=False, width=120, **kwargs):
    return yaml.dump(obj, default_flow_style=default_flow_style, width=width, **kwargs)


def pick_random_item(items, input):
    return items[
        hash(str(input)) % len(items)
        ]


def str2bool(v):
    if v.lower() in ('yes', 'true', '1'):
        return True
    elif v.lower() in ('no', 'false', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')
