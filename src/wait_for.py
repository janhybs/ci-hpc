#!/bin/python3
"""
A simple script which waits for the PBS Job to end. Can also kill the job
if timeout is passed.

The script was tested with PBSPro scheduling system only.
TODO: Add support for other systems
"""

import sys
import time
import subprocess
import progressbar
import re
import argparse

def main(args=None):
    """
    Main function which parses given arguments and wait for the job
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--timeout', '-t', type=int, default=None)
    parser.add_argument('--check-period', type=int, default=10)
    parser.add_argument('pbs_job_id')
    parser_args = parser.parse_args()
    print(parser_args)
    qsub_output = sys.argv[1]
    jid = re.compile('([0-9]+)\.?.*').match(parser_args.pbs_job_id).group(1)

    command = ['qstat', jid]

    print('Using following command to determine Job status')
    print(' '.join(command))
    print('-' * 80)
    kwargs = dict(stderr=subprocess.STDOUT)

    start_time = time.time()
    timeout = parser_args.timeout
    check_period = parser_args.check_period

    # TODO add timeout for the wait command as well
    while subprocess.Popen(command, **kwargs).wait() == 0:
        sys.stdout.flush()
        duration = time.strftime('%H:%M:%S', time.gmtime(int(time.time() - start_time)))
        print('Waiting for %s to finish | runtime: %s' % (jid, duration))
        print('-' * 80)

        for i in range(check_period):
            time.sleep(1)
            if timeout and timeout > 0:
                if (time.time()-start_time) > timeout:
                    print('!' * 80)
                    print('Timeout! Job is still running, but timeout was set to %d seconds' % timeout)
                    print('Using following command to kill the job %s status' % jid)
                    kill_command = ['qdel', jid]
                    print(' '.join(kill_command))
                    print('ended with', subprocess.Popen(kill_command, **kwargs).wait())
                    exit(1)


    print("Job '%s' has finished!" % jid)
    exit(0)

if __name__ == '__main__':
    main()
