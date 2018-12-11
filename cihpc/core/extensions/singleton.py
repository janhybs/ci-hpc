#!/bin/python3
# author: Jan Hybs


class Singleton(type):
    """
    Singleton metaclass pattern

    A metaclass is the class of a class; that is, a class is an instance of its metaclass
    https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def parameter_singleton(cls):
    """ decorator for a class to make a singleton out of it """
    _instances = dict()

    def get(*args, **kwargs):
        """
        creating or just return the one and only class instance.
        The singleton depends on the parameters used in __init__
        """
        key = (cls, args, hash(tuple(sorted(kwargs.items()))))

        if key not in _instances:
            _instances[key] = cls(*args, **kwargs)

        return _instances[key]

    return get


def single_parameter_singleton(cls):
    """ decorator for a class to make a singleton out of it """
    _instances = dict()

    def get(*args, **kwargs):
        """
        creating or just return the one and only class instance.
        The singleton depends on the parameters used in __init__
        """
        key = None

        if args:
            key = args[0]

        if kwargs:
            key = list(kwargs.values())[0]

        if key not in _instances:
            _instances[key] = cls(*args, **kwargs)

        return _instances[key]

    return get
