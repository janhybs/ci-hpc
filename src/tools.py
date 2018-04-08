#!/bin/python3
# author: Jan Hybs


#/lustre/sw/anaconda/anaconda3/bin/python3
# module load anaconda/python3
# module load python-3.6.3-gcc-6.2.0-snvgj45

import itertools
import os
import sys
import subprocess
import time, datetime

# pip install python-dateutil
import dateutil.parser as dparser

import json
import yaml
import random
import re
import threading
from collections import defaultdict

from vcs.git import Git



def groupby(iterable, projection):
    result = defaultdict(list)
    for item in iterable:
        result[projection(item)].append(item)
    return result


class PreparedJob(object):
    def __init__(self):
        self.name = None
        self.pbs = None
        self.before = None
        self.script = None
        self.after = None
        self.collect_spec = None

        self.cpu_count = -1
        self.configuration = None
        self.stdout = None
        self.stderr = None
        self.duration = None
        self.progress_fmt = ''
        self.process = None
        self.timer = None

    def update_info(self):
        while self.process.poll() is None:
            print('\r' + self.progress_fmt.format(self=self), end='')
            time.sleep(1)

    def execute(self):
        script = TempScript(os.path.join('tmp-script.sh'))

        # update time()
        if self.configuration:
            self.configuration['time'] = dict(
                now=time.time(),
                iso=datetime.datetime.now().isoformat()
            )

        with script:
            script.writeline(self.generate_script())

        if self.collect_spec:
            with Timer('install-part') as self.timer:
                self.process = subprocess.Popen(['/bin/bash', script.path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                update_info = threading.Thread(target=self.update_info)
                update_info.start()

                stdout, stderr = self.process.communicate()
                self.stdout = stdout.decode()
                self.stderr = stderr.decode()

            update_info.join()
            print('\r' + self.progress_fmt.format(self=self))
        else:
            with Timer('install-part') as self.timer:
                subprocess.Popen(['/bin/bash', script.path]).wait()

        self.duration = self.timer.duration
        return self.duration

    def collect(self):
        if self.collect_spec:
            collected = list()
            dump_path = None

            for col in self.collect_spec:
                if 'dir' in col:
                    dump_path = os.path.abspath(col['dir'])
                    os.makedirs(dump_path, exist_ok=True)
                    
                    dump_path_ = os.path.abspath(os.path.join(col['dir'], 'stdout'))
                    stdout_file = os.path.join(dump_path_, 'stdout-%d.txt' % time.time())
                    os.makedirs(dump_path_, exist_ok=True)
                    with open(stdout_file, 'w') as fp:
                        fp.write(str(self.stdout))
                        fp.write('\n')
                        fp.write('#############################################')
                        fp.write('\n')
                        fp.write(str(self.stderr))

                candidates = list()
                doctype = dict(json=json.loads, yaml=yaml.load).get(col.get('type', 'json'))

                if 'split' in col:
                    split_seq = col.get('split', '-' * 77)
                    candidates.extend(
                        self.stdout.split(split_seq)
                    )
                else:
                    start_seq, stop_seq = col.get('start', '>>>'), col.get('stop', '<<<')

                    for piece in self.stdout.split(start_seq, 1):
                        if not piece.strip():
                            continue
                        if piece.find(stop_seq) != -1:
                            document = piece.rsplit(stop_seq, 1)[0]
                            if col.get('keep', False):
                                document = start_seq + document + stop_seq
                            candidates.append(document)

                for candidate in candidates:
                    # ignore parse error
                    try: collected_document = doctype(candidate)
                    except: continue

                    # add additional tags to each json
                    tags = col.get('tags', {}).copy()
                    tags = Project.configure(tags, self.configuration)
                    # print(tags)
                    collected_document['tags'] = tags.copy()

                    if 'int_fields' in col:
                        collected_document = convert(collected_document, col['int_fields'], int)

                    if 'float_fields' in col:
                        collected_document = convert(collected_document, col['float_fields'], float)

                    if 'datetime_fields' in col:
                        collected_document = convert(collected_document, col['datetime_fields'], dparser.parse)

                    collected.append(collected_document.copy())

            if dump_path:
                for doc in collected:
                    rnd_name = ('%s.%d.%s.%s' % (
                        self.name,
                        int(time.time()),
                        str(hex(random.randint(0x10000, 0xFFFFF)))[2:],
                        'yaml'
                    )).lower().replace(' ', '-')
                    with open(os.path.join(dump_path, rnd_name), 'w') as fp:
                        yaml.dump(doc, fp, default_flow_style=False)
                        
                if 'database' in col:
                    import pymongo as pm
                    from modules.profilers import ProfilerParser
                    
                    for database in col.get('database', []):
                        if 'mongodb' in database:
                            mongo_config = database.get('mongodb')
                            client = pm.MongoClient(connect=False, **mongo_config)
                            
                            # save the results to db
                            # TODO optimize insert
                            # TODO remove inserted(or add option to)
                            # TODO Singleton pattern to save db transfer
                            with ProfilerParser(client.get_database('cirrus')) as prof:
                                    prof.load_data_from_dir(dump_path)
                                    prof.save_data_to_db()


    def __repr__(self):
        return "<{self.cpu_count}:{self.name}>".format(self=self)

    def generate_script(self):
        parts = [
            '# AUTOGENERATED SCRIPT #',
            ' ',
            self.pbs,
            self.before,
            self.script,
            self.after,
        ]
        return '\n'.join([str(p) for p in parts if p])

class PreparedStep(object):
    def __init__(self, name='<no-name>', description='<no-description>', configuration=dict(variables={})):
        self.name = name
        self.description = description
        self.configuration = configuration
        self.repeat = 1
        self.jobs = list()

    def add_job(self, job):
        if job:
            self.jobs.append(job)

    def execute(self):
        for job in self.jobs:
            print(job)
            times = list()
            for i in range(1, self.repeat + 1):
                job.progress_fmt = "  - {i:02d}/{self.repeat:02d}: {job} [{{self.timer.pretty_duration_micro}}]".format(**locals())
                sys.stdout.flush()
                times.append(job.execute())
                job.collect()
            print(job, 'avg-time: %1.3f' % (sum(times)/len(times)))
            print()

class PreparedJobs(object):
    def __init__(self):
        self.steps = list()

    def add(self, step):
        if step:
            self.steps.append(step)

    def execute(self):
        for prepared_step in self.steps:
            prepared_step.execute()



class SimpleMath(object):
    def __init__(self, value):
        self.value = value

    def __getitem__(self, k):
        return eval(k.replace('?', str(self.value)))

def convert(o, fields, cls):
    def process(o, pts):
        regex = re.compile(pts[0])
        if type(o) is dict:
            for k in o.keys():
                if regex.match(k):
                    if not pts[1:]:
                        try:
                            o[k] = cls(o[k])
                        except:
                            pass
                    else:
                        process(o[k], pts[1:])

        elif type(o) is list:
            for k in o:
                process(k, pts)

    for f in fields:
        pts = f.split('/')
        process(o, pts)
    return o



class TempScript(object):
    def __init__(self, path, shell='#!/bin/bash --login', verbose=False):
        self.path = path
        self.shell = shell
        self.verbose = verbose
        self.fp = None

    def newline(self):
        self.writeline()

    def writeline(self, content=''):
        if content:
            self.fp.write(content)
        self.fp.write('\n')

    def __enter__(self):
        self.fp = open(self.path, 'w+')
        if self.shell:
            self.writeline(self.shell)

        if self.verbose:
            self.writeline('# turn on debugging')
            self.writeline('set -x')

        return self

    def add(self, **lines):
        for line in lines:
            self.writeline(line)

    def remove(self):
        os.remove(self.path)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.fp.close()
        os.chmod(self.path, 0o777)


class Timer(object):
    def __init__(self, name=None):
        self.start_time = None
        self.stop_time = None
        self.name = name

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop_time = time.time()
        return False

    @property
    def duration(self):
        if self.stop_time:
            return self.stop_time - self.start_time
        else:
            return time.time() - self.start_time

    @property
    def pretty_duration(self):
        return time.strftime('%H:%M:%S', time.gmtime(int(self.duration)))

    @property
    def pretty_duration_micro(self):
        micro = ('%1.3f' % (self.duration - int(self.duration)))[2:]
        return time.strftime('%H:%M:%S', time.gmtime(int(self.duration))) + '.' + micro


class Project(object):
    def __init__(self, project, args=None):
        self.project = project
        self.global_args = dict()
        self.name = 'unknown-project'

        workdir = project.get('workdir')
        os.makedirs(workdir, exist_ok=True)
        os.chdir(workdir)
        self.global_args.update(project.get('define', dict()))

        if args:
            self.global_args['arg'] = vars(args)
            self.name = self.global_args['arg'].get('project', 'foo')

    @property
    def installation_parts(self):
        return self.project.get('install', [])

    @property
    def test_suites(self):
        return self.project.get('test', [])

    @classmethod
    def configure(cls, o, d):
        for k in o:
            if type(o[k]) is str:
                o[k] = o[k].format(**d)
            elif type(o[k]) is dict:
                o[k] = cls.configure(o[k], d)
        return o

    @staticmethod
    def _merge_dict(*items, **items2):
        result = dict()
        for item in items:
            result.update(item)

        for k, v in items2.items():
            if k not in result:
                result[k] = dict()
            result[k].update(v)
        return result

    @staticmethod
    def _fix_indent(script):
        """
        Fixes inconsistent indentation
        """
        lines = list()
        first = True
        for line in script.splitlines():
            if first and not line.strip():
                first = False
                continue
            lines.append(line.lstrip())
        return '\n'.join(lines)

    def process_configuration(self, step, config):
        result = list()
        out_file = os.path.abspath('out-temp.log')
        temp_file = TempScript(
            os.path.abspath('install-temp.sh'),
            verbose=step.get('verbose', False)
        )
        verbose = 'set -x' if step.get('verbose', 0) else '# debuging off'

        variables = self._merge_dict(
            self.global_args,
            config,
            step=step,
            time=dict(
                now=time.time(),
                iso=datetime.datetime.now().isoformat()
            )
        )

        cpu_count = -1
        if config:
            for k in config.keys():
                if k.find('cpu') != -1 or k.find('core') != -1:
                    variables[k + '_exec'] = SimpleMath(5)
                    cpu_count = config[k]

        job = PreparedJob()
        job.name = step.get('name', 'no-name').format(**variables)
        job.pbs = step.get('pbs', '').format(**variables)
        job.before = self.project.get('prepare-env', '# EMPTY INIT SCRIPT').format(**variables)
        job.script = step.get('shell', '# no shell ').format(**variables)
        job.after = self.project.get('clean-env', '# EMPTY CLEANUP SCRIPT').format(**variables)
        job.collect_spec = step.get('collect', None)

        job.cpu_count = cpu_count
        job.configuration = variables

        return job

    def process_all_parts(self, parts, name):
        if 'prepare-env' in self.project:
            try:
                prepare_env = self.project['prepare-env'].format(**self.global_args)
                print('=' * 80)
                print('{:->80s}'.format(' PREPARE SCRIPT '))
                print('=' * 80)
                print(prepare_env)
            except Exception as e:
                pass

        jobs = PreparedJobs()
        i, total = 0, len(parts)
        for case in parts:
            i += 1
            print('=' * 80)
            print('{:->80s}'.format(' ' + name.format(**locals()) + ' '))
            print('=' * 80)
            jobs.add(self.process_part(case))
        print('*' * 80)
        return jobs

    def prepare_step(self, step):
        configuration = step.get('configuration', dict(variables={}))
        variables = configuration['variables']
        values = [list(y.values())[0] for y in variables]
        names = [list(y.keys())[0] for y in variables]
        product = list(dict(zip(names, x)) for x in itertools.product(*values))
        return product, names, values

    def process_part(self, step):
        if step.get('enabled', True) is False:
            print('-SKIPPED-')
            return None
        product, names, values = self.prepare_step(step)

        if 'git' in step:
            for git_args in step.get('git', []):
                git_args = self.configure(git_args, self.global_args)
                git = Git(**git_args)
                git.clone()
                git.checkout(
                    git_args.get('commit', ''),
                    git_args.get('branch', 'master'),
                )
                git.info()

        prepared_step = PreparedStep(
            name=step.get('name', '<no-name>'),
            description=step.get('description', '<no-name>'),
            configuration=step.get('configuration', dict(variables={})),
        )
        prepared_step.repeat = step.get('repeat', 1)
        current = 1
        total = len(product)
        jobs = list()

        print('Preparing {total} jobs for case "{prepared_step.name}"'.format(**locals()))
        if product:
            for p in product:
                p.update(dict(_current_=current, _total_=total))
                prepared_step.add_job(
                    self.process_configuration(step, p)
                )
                current += 1
        return prepared_step
