#!/bin/python3
# author: Jan Hybs


import os
import sys
import time
import signal

from daemon import pidfile, DaemonContext


class DaemonException(Exception):
    """Custom exception for :class:`cihpc.common.processing.daemon.Daemon`"""
    pass


class Daemon(object):
    """
    A simple class which enabled system forking and thus running in the background
    """

    def __init__(self, name, pid_file, **kwargs):
        """
        Parameters
        ----------
        name: str
            name of this Daemon
        pid_file: str
            path to the pid will, which will hold the pid of daemon process
        kwargs: dict
            additional arguments passed to the :class:`daemon.DaemonContext` constructor
        """

        self.name = name
        self.pid_file = pid_file
        self.kwargs = kwargs
        self._context = None
        self._pid = None

    def __repr__(self):
        return 'Daemon({self.name}, pid={self.pid}, status={status}, pid_file={self.pid_file})'.format(
            self=self,
            status='running' if self.is_running() else 'stopped'
        )

    def start(self):
        """
        Method will call method run within the daemon context

        Raises
        ------
        DaemonException
            if the process is already running
        """

        if self.is_running():
            raise DaemonException('process is already running [%d]' % self.pid)

        self._context = DaemonContext(
            pidfile=pidfile.TimeoutPIDLockFile(self.pid_file),
            **self.kwargs
        )

        print('[OK] process started, pid will stored in %s' % self.pid_file)

        with self._context:
            self.run()

    def stop(self, graceful_period=3.0):
        """
        Stops the process
        Parameters
        ----------
        graceful_period: float
            if greater than 0, will send SIGINT first and will wait
            at max graceful_period

        Raises
        ------
        DaemonException
            if no pid file exists
        DaemonException
            if no process is running

        Returns
        -------
        int:
            pid of the process which was terminated

        """

        if self.pid is None:
            raise DaemonException('pid file %s does not exists' % self.pid_file)

        if not self.is_running():
            raise DaemonException('process is not running')

        pid = self.pid

        if graceful_period > 0:
            self._send_signal(signal.SIGINT)
            start_time = time.time()

            while (time.time() - start_time) < graceful_period:
                if not self.is_running():
                    # terminated gracefully
                    self._reset()
                    return pid
                time.sleep(0.3)

        # worst case send -9
        self.kill()
        self._reset()
        return pid

    def status(self):
        """
        Checks process status
        Returns
        -------
        bool
            True if the process is up and running
        """

        return self.is_running()

    def debug(self):
        """
        Runs a method run and return is return value.

        No forking or demonizing will be performed
        """
        return self.run()

    @property
    def pid(self):
        if self._pid:
            return self._pid

        try:
            with open(self.pid_file) as fp:
                self._pid = int(fp.read().strip())
                return self._pid
        except:
            return None

    def is_running(self):
        """ Check for the existence of a unix pid. """

        if self.pid is None:
            return False

        try:
            os.kill(self.pid, 0)
        except OSError:
            return False

        return True

    def kill(self):
        """
        Kills the process, sending signal -9


        Raises
        ------
        DaemonException
            if no pid file exists

        Returns
        -------
        bool
            True if signal was sent
        """

        pid = self.pid

        if pid is None:
            raise Exception('pid file %s does not exists' % self.pid_file)

        return self._send_signal(signal.SIGKILL)

    def do_action(self, action):
        """
        Performs given action on this daemon object

        Parameters
        ----------
        action: str
            allowed actions are start, stop, restart, status, debug

        Returns
        -------
        bool
            True if the action succeeded False otherwise
        """

        if action == 'status':
            if self.status():
                print('[OK] Process is running [%d]' % self.pid)
                return True
            else:
                print('[KO] Process is not running')
                return False

        if action == 'start':
            try:
                self.start()
                sys.stdout.write('[OK] process started [%d]\n' % self.pid)
                return True
            except Exception as de:
                sys.stderr.write('[ERROR] %s\n' % de)
                return False

        if action == 'debug':
            return self.debug()

        if action == 'stop':
            try:
                pid = self.stop()
                sys.stdout.write('[OK] process stopped [%d]\n' % pid)
                return True
            except Exception as de:
                sys.stderr.write('[ERROR] %s\n' % de)
                return False

        if action == 'restart':
            try:
                pid = self.stop()
                sys.stdout.write('[OK] process stopped [%d]\n' % pid)
            except Exception as de:
                sys.stderr.write('[ERROR] %s\n' % de)

            try:
                self.start()
                sys.stdout.write('[OK] process started [%d]\n' % self.pid)
                return True
            except Exception as de:
                sys.stderr.write('[ERROR] %s\n' % de)
                return False

        if action == 'kill':
            try:
                self.kill()
                sys.stdout.write('[OK] process killed [%d]\n' % self.pid)
                return True
            except Exception as de:
                sys.stderr.write('[ERROR] %s\n' % de)
                return False

    def _send_signal(self, sig=0):
        try:
            os.kill(self.pid, sig)
        except OSError:
            return False

        return True

    def _reset(self):
        self._pid = None

    def run(self):
        while True:
            import time

            with open('/home/jan-hybs/projects/ci-hpc/.log', 'a') as fp:
                fp.write(str(time.time()))
                fp.write('\n')

            time.sleep(1.0)

        # raise NotImplemented('Method *run* is not implemented!')