#!/bin/python3
# author: Jan Hybs



import sys
import os
import re
import subprocess
import re, sys
import time
import progressbar
import argparse
from dateutil.relativedelta import relativedelta
import utils.config as cfg

__dir__ = os.path.abspath(os.path.dirname(__file__))
__root__ = os.path.dirname(__dir__)
__cfg__ = os.path.join(__root__, 'cfg')
__src__ = os.path.join(__root__, 'src')

config_path = os.path.join(__cfg__, 'variables.yaml')
config = cfg.load_config(config_path)
print(cfg.yaml_dump(config))

cwd = '/home/jan-hybs/projects/fenics-project/hpc-ci'
cwd = '/lustre/home/ec036/janhybs/projects/hpc-ci'
cwd = '/home/jan-hybs/mnt/cirrus/projects/hpc-ci'
cwd = config['hpc-ci-home']


# attrs = ['years', 'months', 'days', 'hours', 'minutes', 'seconds']
# human_readable = lambda delta: [
#     '%d %s' % (getattr(delta, attr), getattr(delta, attr) > 1 and attr or attr[:-1])
#         for attr in attrs if getattr(delta, attr)
# ]

# git log -n 10 --graph '--pretty=format:%h:%ar:%ae:%d:%s'
class GitHash(object):
    def __init__(self,relation, git_hash, rel_date, email, branches, message):
        self.relation = relation
        self.hash = git_hash
        self.rel_date = rel_date
        self.email = email
        self.branches = branches
        self.message = message

        self.branch = 'master'
        self.message_peek = ''
        if message:
            self.message_peek = message[:64]
            if len(self.message_peek) != len(message):
                self.message_peek = message[:60] + ' ...'


def read_process_file(git_file):
    hash_match = re.compile(r'([ |*\\/]+) ([a-f0-9]{6,8})\| ?(.*)')
    result = list()
    with open(git_file, 'r') as fp:
        for line in fp.read().splitlines():
            if line.startswith('#'):
                continue

            match = hash_match.match(line)
            if match:
                relation = match.group(1)
                git_hash = match.group(2)
                rel_date, email, branches, message = [x.strip() for x in match.group(3).split('|', 4)]
                result.append(GitHash(
                    relation, git_hash, rel_date,
                    email, branches, message
                ))
            else:
                result.append(line)
    return result


def trigger_install(git):
    path = os.path.join(cwd, 'tmp-install-%s.log' % git.hash)
    # return subprocess.Popen(['sleep', '1']), None, path
    fp = open(path, 'w')
    return subprocess.Popen([
        'python3', 'src/main.py', 'install',
        '--commit=dolfin:%s' % git.hash,
        '--branch=dolfin:%s' % git.branch,
    ], cwd=cwd, stdout=fp, stderr=subprocess.STDOUT), fp, path


def trigger_tests(git):
    path = os.path.join(cwd, 'tmp-tests-%s.log' % git.hash)
    # return subprocess.Popen(['sleep', '1']), None, path
    fp = open(path, 'w')
    return subprocess.Popen([
        '/bin/bash', 'entrypoint', 'test',
    ], cwd=cwd, stdout=fp, stderr=subprocess.STDOUT), fp, path


def read_last_line(path):
    try:
        p = subprocess.Popen(['tail', '-1', path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        o, e = p.communicate()
        return str(o.decode().strip())
    except Exception:
        return ''

def git_debug_info(common_prefix):
    print(common_prefix, '$> git rev-parse HEAD')
    o, e = subprocess.Popen(
        'git rev-parse HEAD'.split(),
        cwd='/lustre/home/ec036/janhybs/projects/hpc-ci/projects/fenics/dolfin',
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).communicate()
    for l in o.decode().strip().splitlines():
        print(common_prefix, l)
    print(common_prefix)

    print(common_prefix, '$> git log -n 1 --format=fuller --date=relative')
    o, e = subprocess.Popen(
        'git log -n 1 --format=fuller --date=relative'.split(),
        cwd='/lustre/home/ec036/janhybs/projects/hpc-ci/projects/fenics/dolfin',
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).communicate()
    for l in o.decode().strip().splitlines():
        print(common_prefix, l)
    print(common_prefix)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('git_file')
    parser.add_argument('--preview', '-p', action='store_true', default=False)
    args = parser.parse_args()

    no_preview = not args.preview
    result = read_process_file(args.git_file)
    i = 0

    space = ' '
    total = len([x for x in result if type(x) is GitHash])
    len_total = len(str(total))
    for git in result:
        prefix_fmt = '%{len_total}d/%{len_total}d)'.format(len_total=len_total)
        prefix_len = prefix_fmt % (0, 0)
        prefix_fill = ' ' * len(prefix_len)

        if type(git) is GitHash:
            i += 1
            prefix = prefix_fmt % (i, total)
            info = '{prefix} {git.relation:12s} [{git.hash:7s}] {git.message_peek:64} [{git.rel_date}]'
            common_prefix = '{prefix_fill} {git.relation:12s} {space:9s}'.format(**locals())
            # line = '%s %-12s [%6s] %s'% (prefix, git.relation, git.hash, git.message_peek)

            print(info.format(**locals()))
            print(common_prefix)

            # ----------------------------------------------------------------------

            def update_progress(common_prefix, start_time, path):
                duration = time.strftime('%H:%M:%S', time.gmtime(int(time.time() - start_time)))
                print('\r{common_prefix} reading last line ...{space:100s}'.format(space=' ', **locals()), end='')
                last_line = read_last_line(path)[:64]
                print('\r{common_prefix} {last_line:64} [{duration}]'.format(**locals()), end='')
                sys.stdout.flush()

            print(common_prefix, 'Installing ...')
            if no_preview:
                proc, fp, path = trigger_install(git)
                start_time = time.time()
                while proc.poll() is None:
                    update_progress(common_prefix, start_time, path)
                    time.sleep(5)
                if fp: fp.close()
                update_progress(common_prefix, start_time, path)
                print('\n' + common_prefix)

            # ----------------------------------------------------------------------

            if no_preview:
                git_debug_info(common_prefix)

            # ----------------------------------------------------------------------

            print(common_prefix, 'Testing ...')
            if no_preview:
                proc, fp, path = trigger_tests(git)
                start_time = time.time()
                while proc.poll() is None:
                    update_progress(common_prefix, start_time, path)
                    time.sleep(5)
                if fp: fp.close()
                update_progress(common_prefix, start_time, path)
                print('\n' + common_prefix)

            # label = progressbar.FormatCustomText('%(value)s', dict(value='<last-line>'))
            # bar = progressbar.ProgressBar(
            #     term_width=100,
            #     max_value=progressbar.UnknownLength,
            #     widgets=[
            #         line, ' | ', progressbar.Timer(), ' | ', label
            #     ]
            # )
            # while proc.poll() is None:
            #     if path:
            #         try:
            #             p = subprocess.Popen(['tail', '-1', path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            #             o, e = p.communicate()
            #             o = str(o.decode().strip())[:64]
            #             o = o + ' ' * (64-len(o))
            #             label.update_mapping(**dict(value=o))
            #         except Exception as e:
            #             pass
            #
            #     bar.update(0)
            #     time.sleep(5)
            # if fp:
            #     fp.close()
            # bar.finish()
            #
            # # ----------------------------------------------------------------------

            # print(common_prefix)
            # proc = trigger_tests(git)
            # print(proc.wait())

        else:
            print('{prefix_fill} {git}'.format(**locals()))
