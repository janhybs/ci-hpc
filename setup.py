#!/bin/python3
# author: Jan Hybs

import os
import setuptools
import cihpc

__root__ = os.path.dirname(__file__)

# add description
with open(os.path.join(__root__, 'README.md'), 'r') as fp:
    long_description = fp.read()


# specify requirements
with open(os.path.join(__root__, 'requirements.txt'), 'r') as fp:
    REQUIREMENTS = [line for line in fp.read().strip().splitlines() if line]


try:
    long_description = long_description[0:long_description.find('## CI-HPC showcase')].strip()
except:
    long_description = long_description.strip()


PACKAGES = [
  'cihpc',
  'cihpc.core',
  'cihpc.core.structures',
  'cihpc.core.db',
  'cihpc.core.processing',
  'cihpc.core.execution',
  'cihpc.cfg',
  'cihpc.common',
  'cihpc.common.utils',
  'cihpc.common.utils.caching',
  'cihpc.common.utils.git',
  'cihpc.common.utils.git.webhooks',
  'cihpc.common.utils.git.webhooks.push_hook',
  'cihpc.common.utils.files',
  'cihpc.common.logging',
  'cihpc.common.processing',
  'cihpc.common.processing.daemon',
  'cihpc.git_tools',
  'cihpc.git_tools.utils',
  'cihpc.artifacts',
  'cihpc.artifacts.modules',
  'cihpc.www',
  'cihpc.www.rest',
  'cihpc.www.cfg',
  'cihpc.www.engines',
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


SCRIPTS = [
    'bin/cihpc-www',
    'bin/cihpc',
]


setuptools.setup(
    name='cihpc',
    version=cihpc.__version__,

    packages=PACKAGES,
    classifiers=CLASSIFIERS,
    scripts=SCRIPTS,
    install_requires=REQUIREMENTS,
    
    url='https://github.com/janhybs/ci-hpc',
    license='MIT License',

    author='jan-hybs',
    author_email='jan.hybs@tul.cz',


    long_description=long_description,
    long_description_content_type="text/markdown",
    description='Python performance monitoring tool using HPC'
)
