#!/bin/python3
# author: Jan Hybs


import enum
import multiprocessing
import threading
import time
from pluck import pluck
import random
import itertools

from multiproc.complex_semaphore import ComplexSemaphore
from proc.step.step_shell import ProcessConfigCrate
from utils.events import EnterExitEvent
from utils.logging import logger
from utils.timer import Timer


class PoolInt(object):
    def __init__(self, value=0):
        self.value = value

    def __call__(self, *args, **kwargs):
        return self.value


class WorkerStatus(enum.IntEnum):
    RUNNING = 1
    WAITING = 2
    FINISHED = 3


class Worker(threading.Thread):
    def __init__(self, crate, semaphore, thread_event, target, cpus=1):
        super(Worker, self).__init__()
        self.cpus = cpus                    # type: int
        self.semaphore = semaphore          # type: ComplexSemaphore
        self.thread_event = thread_event    # type: EnterExitEvent
        self.target = target                # type: callable
        self.crate = crate                  # type: ProcessConfigCrate
        self.result = None
        self.cpus = cpus
        self.status = WorkerStatus.WAITING  # random.choice(list(WorkerStatus))
        self.timer = Timer(self.name)

    def _run(self):
        self.result = self.target(self)

    def run(self):
        self.semaphore.acquire(value=self.cpus)
        self.status = WorkerStatus.RUNNING
        self.thread_event.on_enter(self)

        with self.timer:
            self._run()

        self.status = WorkerStatus.FINISHED
        self.semaphore.release(value=self.cpus)

    def __repr__(self):
        return '{self.name}({self.cpus}x, [{self.status}])'.format(self=self)


class WorkerPool(object):
    def __init__(self, items, processes, target):
        self.items = items
        self.processes = processes or multiprocessing.cpu_count()
        self.semaphore = ComplexSemaphore(self.processes)
        self.thread_event = EnterExitEvent('thread')
        self.threads = list()
        
        logger.info('process limit set to %d' % self.processes)
        for item in items:
            self.threads.append(
                Worker(
                    crate=item,
                    semaphore=self.semaphore,
                    thread_event=self.thread_event,
                    target=target
                )
            )

    def update_cpu_values(self, target):
        for thread in self.threads:
            thread.cpus = target(thread)

    @property
    def result(self):
        return pluck(self.threads, 'result')

    def start_serial(self):
        for thread in self.threads:
            thread.start()
            thread.join()
            self.thread_event.on_exit(thread)

    def start_parallel(self):
        for thread in self.threads:
            thread.start()

        for thread in self.threads:
            thread.join()
            self.thread_event.on_exit(thread)

        return self.result

    def _print_statuses(self, format='simple'):
        status_getter = lambda x: x[1]
        statuses = pluck(self.threads, 'crate.name', 'status', 'cpus', 'timer')
        sorted_statuses = sorted(statuses, key=status_getter)

        if format == 'simple':
            msg = 'Worker statuses:\n'
            msgs = list()
            for key, group in itertools.groupby(sorted_statuses, key=status_getter):
                grp = list(group)
                if key is WorkerStatus.RUNNING:
                    msgs.append('  %2d x %s %s' % (len(grp), key.name, [x[0] for x in grp]))
                else:
                    msgs.append('  %2d x %s' % (len(grp), key.name))
            logger.info(msg + '\n'.join(msgs), skip_format=True)
        elif format == 'complex':
            msg = 'Worker statuses:\n'
            msgs = list()
            for key, group in itertools.groupby(sorted_statuses, key=status_getter):
                msgs.append('%s:' % key.name)
                for name, status, cpus, timer in group:
                    if timer.duration > 0.0:
                        msgs.append(' - %dx %s [%1.3f sec]' % (cpus, name, timer.duration))
                    else:
                        msgs.append(' - %dx %s' % (cpus, name))
            logger.info(msg + '\n'.join(msgs), skip_format=True)
        elif format == 'oneline':
            statuses = sorted([x[0] for x in pluck(self.threads, 'status.name')])
            msg = ''.join(statuses).upper().replace('W', '◦').replace('R', '▸').replace('F', ' ') # ⧖⧗⚡
            logger.info(' - ' + msg, skip_format=True)

    def log_statuses(self, log_period=None, update_period=0.9, format=None):
        if format is None:
            if len(self.threads) > 20:
                format = 'oneline'
            elif len(self.threads) > 5:
                format = 'simple'
            else:
                format = 'complex'
        
        if log_period is None:
            if format == 'oneline':
                log_period = 1.0
            else:
                log_period = 5.0
        
        def target():
            last_print = 0
            while True:
                if (time.time() - last_print) > log_period:
                    self._print_statuses(format)
                    last_print = time.time()

                if set(pluck(self.threads, 'status')) == {WorkerStatus.FINISHED} or not self.threads:
                    break
                time.sleep(update_period)

        thread = threading.Thread(target=target)
        thread.start()