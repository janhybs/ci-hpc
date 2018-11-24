#!/usr/bin/python
# author: Jan Hybs


"""
A simple script which waits for the PBS Job to end. Can also kill the job
if timeout is passed.

The script was tested with PBSPro scheduling system only.
TODO: Add support for other systems
"""

import sys
import threading
import time
import subprocess
import re
import argparse
import os


def main(args=None):
    """
    Main function which parses given arguments and wait for the job
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--timeout', '-t', type=int, default=None)
    parser.add_argument('--check-interval', type=int, default=10)
    parser.add_argument('--live-log', type=str, default=None,
                        help='If set, will also print lines from the live log file')
    parser.add_argument('--quiet', default=False, action='store_true', help='If set, suppresses qsub output')
    parser.add_argument('pbs_job_id')
    parser_args = parser.parse_args()
    print(parser_args)
    jid = re.compile('([0-9]+)\.?.*').match(parser_args.pbs_job_id).group(1)

    command = ['qstat', jid]

    print('Using following command to determine Job status')
    print(' '.join(command))
    print('-' * 80)
    kwargs = dict(stderr=subprocess.STDOUT)

    if parser_args.quiet:
        kwargs.update(dict(stdout=subprocess.DEVNULL))

    start_time = time.time()
    timeout = parser_args.timeout
    check_interval = parser_args.check_interval

    # print log file if set
    reader = None
    if parser_args.live_log:
        reader = LiveReader(
            file_path=parser_args.live_log,
            callback=CountPrint().print_line,
            update_interval=check_interval,
            wait_for_file=True)
        reader.start()

    # TODO add timeout for the wait command as well
    while subprocess.Popen(command, **kwargs).wait() == 0:
        sys.stdout.flush()
        duration = time.strftime('%H:%M:%S', time.gmtime(int(time.time() - start_time)))
        print('Waiting for %s to finish | runtime: %s' % (jid, duration))

        for i in range(check_interval):
            time.sleep(1)
            if timeout and timeout > 0:
                if (time.time() - start_time) > timeout:
                    print('!' * 80)
                    print('Timeout! Job is still running, but timeout was set to %d seconds' % timeout)
                    print('Using following command to kill the job %s status' % jid)
                    kill_command = ['qdel', jid]
                    print(' '.join(kill_command))
                    print('ended with', subprocess.Popen(kill_command, **kwargs).wait())
                    exit(1)

    print("Job '%s' has finished!" % jid)
    if reader:
        reader.stop()
        reader.join()
    exit(0)


class CountPrint(object):
    """
    Simple class which can print formatter lines and keep track of the no of lines
    """

    def __init__(self, format='[%4d]    %s', counter=1):
        self.format = format
        self.counter = counter

    def print_line(self, line):
        print(self.format % (self.counter, line))
        self.counter += 1


def live_read(fp, update_interval=2.5):
    """
    Function will iterate over a file pointer and will yield file lines
    stops only if file pointer is closed
    :type update_interval: float
    :type fp: typing.TextIO
    """
    while True:
        # if the fp is closed, end the iteration
        if fp.closed:
            raise StopIteration

        # read next line, if there is next line
        # it will ends with a newline (\n)
        # otherwise it will be an empty string
        line = fp.readline()
        if not line:
            time.sleep(update_interval)
            continue

        # yields next line without newline at the end
        yield line[:-1]


class LiveReader(threading.Thread):
    """
    Simple class reading files, which are still appended

    :type file_path: str
    :type file_pointer: typing.TextIO
    :type update_interval: float

    usage:
    ```
        >>> reader = LiveReader('logs/log.txt', print)
        >>> reader.start()
        >>> time.sleep(5)
        >>> reader.stop()
        >>> reader.join()
    ```
    """

    def __init__(self, file_path, callback, update_interval=1.0, wait_for_file=False):
        """
        Parameters
        ----------
        file_path : str
                    file path to the file which is to be read

        callback : builtins.callable
                    callback function which will be called for every new line
                    function should look like this:

                   ``def callback(line)``:

        update_interval : float
                    Update interval in seconds (can be float)
        """
        self.file_path = file_path
        self.file_pointer = None
        self.update_interval = update_interval
        self.callback = callback
        self.wait_for_file = wait_for_file
        self._exit = False
        super(LiveReader, self).__init__(name='live-reader')

    def stop(self):
        self._exit = True
        if self.file_pointer:
            self.file_pointer.close()

    def run(self):
        if not os.path.exists(self.file_path):
            if self.wait_for_file:
                while not self._exit:
                    if os.path.exists(self.file_path):
                        break
                    time.sleep(self.update_interval)

        if not os.path.exists(self.file_path):
            return

        self.file_pointer = open(self.file_path, 'r')
        for line in live_read(self.file_pointer, self.update_interval):
            self.callback(line)


if __name__ == '__main__':
    main()
