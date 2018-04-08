#!/bin/python3
# author: Jan Hybs

import os

import progressbar
import yaml
import collections
import subprocess
import datetime
import pandas as pd

dolfin_repo = '/home/jan-hybs/projects/fenics-project/dolfin'
dolfinx_repo = '/home/jan-hybs/projects/fenics-project/dolfinx'

# dolfin_repo = dolfinx_repo

def try_run_cmd(cmd, dirs, **kwargs):
    for cwd in dirs:
        try:
            o = subprocess.check_output(cmd, cwd=cwd)
            return o.decode().strip()
        except:
            pass
    raise Exception('No valid location found for the command %s' + str(cmd))
        
    

def flatten(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def find(dir, extension='*.yaml'):
    return [os.path.join(dir, x) for x in subprocess.Popen(
        ['find', '-name', extension], cwd=dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).communicate()[0].decode().strip().splitlines()]


class ProfilerParser(object):
    """
    :type df: pandas.core.frame.DataFrame
    """
    def __init__(self, db=None):
        """
        :type db: pymongo.database.Database
        """
        self.db = db
        self.bench = bench = db.get_collection('bench')
        self.items = list()
        self.commits = dict(timestamp=dict(), datetime=dict())
        self.frame_ids = dict()
        self.df = None

    def extract_from_commit(self, commit, prop):
        if commit in self.commits[prop]:
            return self.commits[prop][commit]

        if prop == 'timestamp':
            cmd = 'git show -s --format=%ct'.split() + [commit]
            out = try_run_cmd(cmd, [dolfin_repo, dolfinx_repo])
            self.commits[prop][commit] = int(out)

        if prop == 'datetime':
            cmd = 'git show -s --format=%ct'.split() + [commit]
            out = try_run_cmd(cmd, [dolfin_repo, dolfinx_repo])
            self.commits[prop][commit] = datetime.datetime.fromtimestamp(float(out))

        return self.commits[prop][commit]

    def unwind(self, y):
        result = list()

        frames = y.pop('frames', [])
        libs = y.pop('libs', [])
        common = flatten(y)
        
        # print(common['tags_problem_scale'], common['tags_problem_type'], common['tags_cpu_count'])

        for lib in libs:
            for key in lib.keys():
                common['lib_{lib[name]}_{key}'.format(**locals())] = lib[key]

        if 'lib_dolfin_commit' in common:
            common['commit_timestamp'] = self.extract_from_commit(common['lib_dolfin_commit'], 'timestamp')
            common['commit_datetime'] = self.extract_from_commit(common['lib_dolfin_commit'], 'datetime')

        for f in frames:
            common.update(f)
            result.append(common.copy())

        return result

    def load_frame_ids(self):
        return [x['frame_id'] for x in self.bench.find({}, {'frame_id': 1, '_id': 0})]

    def remove_data(self):
        return self.bench.remove({})

    def load_data_from_db(self):
        self.items = list(self.bench.find({}))

    def save_data_to_db(self):
        ids = list(self.load_frame_ids())

        filtered = [x for x in self.items if x['frame_id'] not in ids]
        print('Found %d frames, %d unique will be inserted' % (len(self.items), len(filtered)))

        if filtered:
            result = self.bench.insert_many(
               filtered
            )
            print(result.acknowledged)
            print(result.inserted_ids)

    def load_data_from_file(self, path):
        with open(path, 'r') as fp:
            y = yaml.load(fp)
        filename = os.path.basename(path)

        for i in self.unwind(y):
            frame_id = '%s-%s' % (i['name'], filename)
            i['frame_id'] = frame_id
            if frame_id not in self.frame_ids:
                self.items.append(i)
                self.frame_ids[frame_id] = True
            else:
                print('duplicate', frame_id)

    def load_data_from_dir(self, dir):
        files = find(dir)
        for file in progressbar.ProgressBar()(files):
            self.load_data_from_file(file)

    def save_data_to_csv(self, name='data.csv'):
        if self.df is None:
            self.finalize()
        self.df.to_csv(name)

    def load_data_from_csv(self, name='data.csv'):
        self.df = pd.read_csv(name, index_col=0)

    def finalize(self):
        self.df = pd.DataFrame(self.items)
        if 'commit_timestamp' in self.df:
            keys = sorted(list(set(self.df['commit_timestamp'])), reverse=True)
            vals = list(range(len(keys)))
            self.df['commit_datetime_id'] = self.df['commit_timestamp'].replace(dict(zip(keys, vals)))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.df is None:
            self.finalize()

        return False
