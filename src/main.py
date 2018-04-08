#!/lustre/sw/anaconda/anaconda3/bin/python3
# module load anaconda/python3
# module load singularity/2.4
# module load python-3.6.3-gcc-6.2.0-snvgj45
#/bin/python


# python3 main.py --commit "bf39fb3933bc96061a9cdece73835ac66e171d5a" --branch "origin/master" --repo "https://github.com/janhybs/HPC-CI.git"

import re
import argparse
import os
from tools import Project, Timer
from collections import defaultdict

import utils.config as cfg

__dir__ = os.path.abspath(os.path.dirname(__file__))
__root__ = os.path.dirname(__dir__)
__cfg__ = os.path.join(__root__, 'cfg')
__src__ = os.path.join(__root__, 'src')


variables_path = os.path.join(__cfg__, 'variables.yaml')
config_path = os.path.join(__cfg__, 'config.yaml')


parser = argparse.ArgumentParser()
parser.add_argument('-b', '--branch', action='append', type=str, default=[])
parser.add_argument('-c', '--commit',  action='append', type=str, default=[])
parser.add_argument('-p', '--project', type=str, default='dolfin')
parser.add_argument('--cpu-count', type=str, default='[1, 2]')
parser.add_argument('step', type=str, nargs='*', default=['install', 'test'])

args = parser.parse_args()


# convert list ["key:value", "key2:value2", ...] to dict {key:value, key2:value2}
# default value for this dictionary is string value 'master'
args.branch = dict(tuple(d.split(':', 1)) for d in args.branch)
args.branch = defaultdict(lambda: 'master', **args.branch)

# default value for this dictionary is string value ''
args.commit = dict(tuple(d.split(':', 1)) for d in args.commit)
args.commit = defaultdict(lambda: '', **args.commit)


variables = cfg.load_config(variables_path)
variables['cpu-count'] = args.cpu_count

# load config
config = cfg.configure_file(config_path, variables)
print(cfg.yaml_dump(config))

# get configuration for the given project and
# convert all single braces ${} with double ${{}}

project_config = config[args.project]
project = Project(project_config, args)
# project_config = cfg.yaml_load(
#     re.sub('\$\{(.*)\}', r'${{\1}}', cfg.yaml_dump(config[args.project]))
# )



# -----------------------------------------------------------------

if 'install' in args.step:
    jobs = project.process_all_parts(
        project.installation_parts,
        'Installation part {i:02d}/{total:02d}'
    )
    jobs.execute()
    exit(0)

if 'test' in args.step:
    jobs = project.process_all_parts(
        project.test_suites,
        'Test suite {i:02d}/{total:02d}',
    )
    jobs.execute()
    exit(0)

    # i = 0
    # for suite in suites:
    #     i += 1
    #     print('{i}) {suite[name]} ({suite[description]})'.format(**locals()))
    #     variables = [list(v.keys())[0] for v in suite['configuration']['variables']]
    #
    #     j = 0
    #     for case in suite['results']:
    #         j += 1
    #         number = '{i}.{j})'.format(**locals())
    #         config = ', '.join(['{k}: {v}'.format(k=k, v=case['variables'][k]) for k in variables])
    #         duration = case['duration']
    #         print('  {number:5s} {duration:1.3f} sec | {config:80s}'.format(**locals()))

#
# if 'test' in args.step:
#     i, total = 0, len(project['test'])
#     tests = list()
#     for step in project['test']:
#         i += 1
#         print('Test {i:02d}/{total:02d}'.format(**locals()))
#         print('=' * 80)
#         tests.append(process_step(project, step))
#
#     # product, names, values = prepare_step(project, project['test'])
#     def pprint(o):
#         if type(o) is dict:
#             return '['+','.join([])+']'
#
#     print('*' * 80)
#     for t in tests:
#         for st in t:
#             names = [k for k,v in st['vars'].items() if not k.startswith('_')]
#             values = [st['vars'][k] for k in names]
#
#             for j in range(len(names)):
#                 print('{k}:{v}'.format(k=names[j], v=values[j]), end='')
#             # tags = ['{k:s}: {v:s}'.format(k=str(k), v=str(v)) for k,v in vars.items()]
#             # print(yaml.dump(vals, default_flow_style=False))
#             # print('{name:10s} [{tags_str}]: {duration:1.3f}'.format(tags_str=', '.join(tags), **st))
#         print('')
