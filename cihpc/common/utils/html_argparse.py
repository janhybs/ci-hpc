#!/bin/python3
# author: Jan Hybs
import argparse


def dict_type(autoconvert=True):
    """
    Describes a dict type, where arguments are in the following format:
    --arg=key=value --arg key2=value2

    will return Namespace(arg={'key': 'value', 'key2': 'value2'}
    """

    class customAction(argparse.Action):

        default_map = dict(
            true=True,
            false=False,
            none=None,
            null=None,
            undefined=None
        )

        def __call__(self, parser, args, values, option_string=None):
            result_dict = getattr(args, self.dest) or dict()

            split = values.split('=', 1)
            # if no arg is specified, will set to True
            if len(split) == 1:
                result_dict[split[0]] = True
            elif len(split) == 2:
                k, v = split[0], split[1]

                if autoconvert:
                    if v.lower() in customAction.default_map:
                        v = customAction.default_map[v.lower()]
                    else:
                        try:
                            v = int(v)
                        except Exception as e:
                            try:
                                v = float(v)
                            except Exception as e:
                                v = v

                result_dict[k] = v

            setattr(args, self.dest, result_dict)

    return customAction


class HTMLArgparse(argparse.ArgumentParser):
    ACTION_DICT = dict_type(autoconvert=True)

    @staticmethod
    def type_str2bool(value):
        if str(value).lower() in ('yes', 'true', '1'):
            return True
        elif str(value).lower() in ('no', 'false', '0'):
            return False
        else:
            raise argparse.ArgumentTypeError('Boolean value expected.')

    def parse_html_args(self, html_string, separator=','):
        """
        :param separator: str
        :type html_string: str
        """
        return self.parse_args(html_string.split(separator))

    def __init__(self):
        super(HTMLArgparse, self).__init__()
