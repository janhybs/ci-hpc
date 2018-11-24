#!/bin/python3
# author: Jan Hybs

import os
import setuptools

__root__ = os.path.dirname(__file__)

with open(os.path.join(__root__, 'README.md'), 'r') as fp:
    long_description = fp.read()


try:
    long_description = long_description[0:long_description.find('## CI-HPC showcase')].strip()
except:
    long_description = long_description.strip()

packages = [
    "cihpc",
    "cihpc.cfg",
    "cihpc.utils",
    "cihpc.vcs",
    "cihpc.structures",
    "cihpc.defaults",
    "cihpc.visualisation",
    "cihpc.processing",
    "cihpc.utils.caching",
    "cihpc.utils.files",
    "cihpc.vcs.webhooks",
    "cihpc.vcs.webhooks.push_hook",
    "cihpc.visualisation.jupyter",
    "cihpc.visualisation.www",
    "cihpc.visualisation.www.rest",
    "cihpc.processing.multi_processing",
    "cihpc.processing.deamon",
    "cihpc.processing.step"
]


setuptools.setup(
    name='cihpc',
    version='0.1.0',
    packages=packages,
    url='https://github.com/janhybs/ci-hpc',
    license='MIT License',
    author='jan-hybs',
    author_email='jan.hybs@tul.cz',
    long_description=long_description,
    long_description_content_type="text/markdown",
    description='A framework combining CI and HPC together with a minimalistic set of Python scripts '
                'to monitor scalability and performance of the software package'
)
