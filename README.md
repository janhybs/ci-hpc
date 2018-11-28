# CI & HPC &middot; [![Travis (.org) branch](https://img.shields.io/travis/janhybs/ci-hpc/dev.svg?style=flat-square)](https://travis-ci.org/janhybs/ci-hpc) [![Read the Docs](https://img.shields.io/readthedocs/ci-hpc/dev.svg?style=flat-square)](https://ci-hpc.readthedocs.io/en/dev) [![download the PDF Docs](https://img.shields.io/badge/docs-PDF-d3231c.svg?style=flat-square&logo=adobe&logoColor=white)](https://readthedocs.org/projects/ci-hpc/downloads/pdf/dev/) [![PyPI](https://img.shields.io/pypi/v/cihpc.svg?style=flat-square)](https://pypi.org/project/cihpc/) [![GitHub](https://img.shields.io/github/license/janhybs/ci-hpc.svg?style=flat-square)](https://github.com/janhybs/ci-hpc/blob/master/LICENSE) [![Coveralls github branch](https://img.shields.io/coveralls/github/janhybs/ci-hpc/dev.svg?style=flat-square)](https://coveralls.io/github/janhybs/ci-hpc)

A *simple* framework which can monitor the performance and scalability of software packages.
The framework presented here combines *Continuous Integation* & *High Performance Computing*
together with a minimalistic set of Python scripts.
The results can be visualised in form of static Jupyter notebook or in an interactive web page.


## Features
 - automatically run benchmarks of your project
 - inspect performance and scalability of your project
 - create complex configurations with travis-like syntax build matrix capabilities (`YAML` format)
 
## How to use ci-hpc?
 1) create a configuration for your repository. In this cofiguration, you should specify several options.
  - `ci-hpc` need to know, which repositories are part of your project
  - you also need to tell the `ci-hpc` how to install your project.  
    It can be as simple as `./configure; make; make install`  
    or  `pip install ./foo/`
    
    But it can be also quite complex, you can even simplify entire process with usage of install file:  
    with something like this`!sh install.sh` (`install.sh` in this case is a shell script, which contains
    your installation process)
    
  - next thing is testing section. Here, we need to know, what benchmarks you want to run under what configuration.
    You can create complex build matrices so your configuration can be kept simple and transparent.
  
  - and finally we need to know, what results you want to store. Is it a some `json` profiler, `yaml` results?
    or are the timings save in a `xml` format? In the `ci-hpc` there is some general support for the `json` and `yaml`
    formats, but you can write your own `artifact` module and simply put it in the correct folder. The most if 
    the heavy lifting is already implemented in the parent class, so it should easier.  

## What's new?
 - now supporting multiple repositories within single project
 - speed up testing process by using multiple cores on a computing node
 - easily run ci-hpc on a previous commits by using `commit-browser` module
 - automatically determine which tests to run based on results in your database
 - webhook support, automatically start `ci-chp` upon new commit

## CWhat's to come?
 - run extra tests when suspecting significant performance change
 - create web visualisation configuration from analyzing records in database

## CI-HPC showcase

### Interactive website

- ![Demo site 1](docs/imgs/demo/demo-01.png)
- ![Demo site 2](docs/imgs/demo/demo-03.png)
- ![Demo site 2](docs/imgs/demo/demo-05.png)
- ![Demo site gif](docs/imgs/ci-hpc-demo-dev.gif)


## Documentation & Installation
Read the docs at [ci-hpc.readthedocs.io](https://ci-hpc.readthedocs.io/en/dev/) to know more about installation.
