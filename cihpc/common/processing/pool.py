#!/bin/python3
# author: Jan Hybs


import enum
import itertools
import logging
import multiprocessing
import threading
import time

from pluck import pluck

from cihpc.common.processing import ComplexSemaphore
from cihpc.common.utils.events import EnterExitEvent
from cihpc.common.utils.timer import Timer


logger = logging.getLogger(__name__)


class PoolInt(object):
    def __init__(self, value=0):
        self.value = value

    def __call__(self, *args, **kwargs):
        return self.value


class WorkerStatus(enum.IntEnum):
    CREATED = 0
    RUNNING = 1
    WAITING = 2
    EXITING = 3
    FINISHED = 4


class LogStatusFormat(enum.Enum):
    AUTO = None
    SIMPLE = 'simple'
    COMPLEX = 'complex'
    ONELINE = 'oneline'
    ONELINE_GROUPED = 'oneline-grouped'


class Worker(threading.Thread):
    def __init__(self, crate, semaphore, thread_event, target, cpus=1):
        super(Worker, self).__init__()
        self.cpus = cpus  # type: int
        self.semaphore = semaphore  # type: ComplexSemaphore
        self.thread_event = thread_event  # type: EnterExitEvent
        self.target = target  # type: callable
        self.crate = crate  # type: cihpc.processing.step.step_shell.ProcessConfigCrate
        self.result = None  # type: cihpc.processing.step.step_shell.ProcessStepResult or any
        self._status = None
        self.status = WorkerStatus.CREATED  # random.choice(list(WorkerStatus))
        self.timer = Timer(self.name)

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        # logger.debug('[%s]%s -> %s' % (str(self), str(self._status), str(value)))
        self._status = value

    def _run(self):
        self.result = self.target(self)

    def run(self):
        self.status = WorkerStatus.WAITING
        self.semaphore.acquire(value=self.cpus)
        self.status = WorkerStatus.RUNNING
        self.thread_event.on_enter(self)

        with self.timer:
            self._run()

        self.semaphore.release(value=self.cpus)
        self.status = WorkerStatus.EXITING

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
        # in serial mode, we start the thread, wait for finish and fire on_exit
        for thread in self.threads:
            thread.start()
            thread.join()
            thread.status = WorkerStatus.FINISHED
            self.thread_event.on_exit(thread)

    def start_parallel(self):
        if self.processes == 1:
            return self.start_serial()

        # start
        for thread in self.threads:
            thread.start()

        # wait
        for thread in self.threads:
            thread.join()
            thread.status = WorkerStatus.FINISHED

        # fire on_exit
        for thread in self.threads:
            self.thread_event.on_exit(thread)

        return self.result

    def _print_statuses(self, format):
        status_getter = lambda x: x[1]
        statuses = pluck(self.threads, 'crate.name', 'status', 'cpus', 'timer')
        sorted_statuses = sorted(statuses, key=status_getter)

        if format is LogStatusFormat.SIMPLE:
            msg = 'Worker statuses:\n'
            msgs = list()
            for key, group in itertools.groupby(sorted_statuses, key=status_getter):
                grp = list(group)
                if key is WorkerStatus.RUNNING:
                    msgs.append('  %2d x %s %s' % (len(grp), key.name, [x[0] for x in grp]))
                else:
                    msgs.append('  %2d x %s' % (len(grp), key.name))
            logger.info(msg + '\n'.join(msgs))

        elif format is LogStatusFormat.COMPLEX:
            msg = 'Worker statuses:\n'
            msgs = list()
            for key, group in itertools.groupby(sorted_statuses, key=status_getter):
                msgs.append('%s:' % key.name)
                for name, status, cpus, timer in group:
                    if timer.duration > 0.0:
                        msgs.append(' - %dx %s [%1.3f sec]' % (cpus, name, timer.duration))
                    else:
                        msgs.append(' - %dx %s' % (cpus, name))
            logger.info(msg + '\n'.join(msgs))

        elif format is LogStatusFormat.ONELINE:
            statuses = sorted([x[0] for x in pluck(self.threads, 'status.name')])
            msg = ''.join(statuses).upper()  # .replace('W', '◦').replace('R', '▸').replace('F', ' ') # ⧖⧗⚡
            logger.info(' - ' + msg)

        elif format is LogStatusFormat.ONELINE_GROUPED:
            statuses = sorted([x for x in pluck(self.threads, 'status')])
            msg = list()
            for g, d in itertools.groupby(statuses):
                msg.append('[%d x %s]' % (len(list(d)), g.name))
            logger.info(' - ' + ' > '.join(msg))

    def log_statuses(self, log_period=None, update_period=0.9, format=LogStatusFormat.AUTO):
        if format is None:
            if len(self.threads) > 40:
                format = LogStatusFormat.ONELINE_GROUPED
            elif len(self.threads) > 20:
                format = LogStatusFormat.ONELINE
            elif len(self.threads) > 5:
                format = LogStatusFormat.SIMPLE
            else:
                format = LogStatusFormat.COMPLEX

        if isinstance(format, str):
            format = LogStatusFormat(format)

        if log_period is None:
            if format is LogStatusFormat.ONELINE:
                log_period = 2.0
            elif format is LogStatusFormat.ONELINE_GROUPED:
                log_period = 5.0
            else:
                log_period = 5.0

        def target():
            # no work to be done? just finish up here
            # and return the thread
            if not self.threads:
                return

            last_print = 0
            while True:
                if (time.time() - last_print) > log_period:
                    self._print_statuses(format)
                    last_print = time.time()

                if set(pluck(self.threads, 'status')) == {WorkerStatus.FINISHED}:
                    break
                time.sleep(update_period)

        thread = threading.Thread(target=target)
        thread.start()
        return thread
