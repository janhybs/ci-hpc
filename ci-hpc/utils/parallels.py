#!/bin/python3
# author: Jan Hybs

# value which can be considered as plentiful cpus available

PLENTY_OF_CPUS = 64  # turn off for now


def extract_cpus_from_worker(worker):
    """
    :type worker: multiproc.thread_pool.Worker
    :return:
    """
    if worker and worker.crate and worker.crate.vars:
        return int(worker.crate.vars.get('__cpu__', 1))

    return 1


def parse_cpu_property(value):
    cpus = 1
    if value in (None, False):
        cpus = 1

    elif str.isdigit(value):
        cpus = int(value)

    return cpus


def determine_cpus(hint=None):
    import multiprocessing
    import math

    try:
        cpu_count = multiprocessing.cpu_count()
    except:
        cpu_count = 1

    # if hint is all, full or null
    # we well try to use as many cpus as possible
    if str(hint).lower() in ('none', 'all', 'full'):
        cpus = cpu_count

    # when we desire half
    # we take 'bigger' half
    elif hint in (1 / 2, 'half'):
        cpus = math.ceil(cpu_count / 2)

    # percent format
    # we always take bigger part
    elif str(hint).endswith('%'):
        percent = float(str(hint)[:-1]) / 100
        cpus = math.ceil(cpu_count * percent)

    # when float is given, we are assuming value <0.0, 1.0>
    # representing percent value
    elif isinstance(hint, float):
        cpus = math.ceil(cpu_count * hint)

    # integer value is directly translated to cpu value
    elif isinstance(hint, int):
        cpus = int(hint)

    # unknown format will result in single core used
    else:
        cpus = 1

    # limit the values of cpus
    cpus = max(min(cpus, cpu_count), 1)

    # if we have plenty of cpus, we remove one cpu so system stuff can be running easily
    # https://stackoverflow.com/questions/20039659/python-multiprocessings-pool-process-limit/20039972
    if cpu_count >= PLENTY_OF_CPUS and cpus >= PLENTY_OF_CPUS:
        cpus -= 1

    # limit the values of cpus once again
    # in case some more complex adjustments were applied
    cpus = max(min(cpus, cpu_count), 1)

    return cpus
