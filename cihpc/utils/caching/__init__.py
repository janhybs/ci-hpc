#!/bin/python3
# author: Jan Hybs

from cihpc.cfg.config import global_configuration


try:
    import cachetools


    def cached():
        return cachetools.cached(**cache_configuration())


    def cache_configuration():
        if global_configuration.cache_type:
            cache = getattr(cachetools, global_configuration.cache_type)
            if global_configuration.cache_opts:
                return dict(cache=cache(**global_configuration.cache_opts))
            return dict(cache=cache())
        return dict(cache=None)

except ImportError:

    def cached():
        def decorator(func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return decorator
