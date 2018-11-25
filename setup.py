#!/bin/python3
# author: Jan Hybs

import os
import setuptools

__root__ = os.path.dirname(__file__)

with open(os.path.join(__root__, 'README.md'), 'r') as fp:
    long_description = fp.read()

with open(os.path.join(__root__, 'version'), 'r') as fp:
    VERSION = fp.read().strip()


try:
    long_description = long_description[0:long_description.find('## CI-HPC showcase')].strip()
except:
    long_description = long_description.strip()

PACKAGES = [
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


CLASSIFIERS = [
    'Development Status :: 4 - Beta',
    'Intended Audience :: Science/Research',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Topic :: Software Development',
    'Topic :: Software Development :: Testing',
    'Topic :: Scientific/Engineering :: Visualization',
    'Operating System :: Microsoft :: Windows',
    'Operating System :: POSIX',
    'Operating System :: Unix',
    'Operating System :: MacOS',
]


setuptools.setup(
    name='cihpc',
    version=VERSION,

    packages=PACKAGES,
    classifiers=CLASSIFIERS,

    url='https://github.com/janhybs/ci-hpc',
    license='MIT License',

    author='jan-hybs',
    author_email='jan.hybs@tul.cz',


    long_description=long_description,
    long_description_content_type="text/markdown",
    description='Python performance monitoring tool using HPC'
)
