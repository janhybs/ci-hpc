#!/usr/bin/python
# author: Jan Hybs


def merge_dict(*items, **items2):
    result = dict()
    for item in items:
        result.update(item)

    for k, v in items2.items():
        if k not in result:
            result[k] = dict()
        result[k].update(v)
    return result


def iter_over(iterable):
    """
    Method will iterate over given iterable and yields
    next iterable value, current index of iteration (from 0), iterable length
    :param iterable:
    :return:
    """
    current = 0
    total = len(iterable)
    for value in iterable:
        yield value, current, total
        current += 1