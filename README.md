# CI & HPC &middot; [![Travis (.org) branch](https://img.shields.io/travis/janhybs/ci-hpc/dev.svg?style=flat-square)](https://travis-ci.org/janhybs/ci-hpc) [![Read the Docs](https://img.shields.io/readthedocs/ci-hpc/dev.svg?style=flat-square)](https://ci-hpc.readthedocs.io/en/dev) [![download the PDF Docs](https://img.shields.io/badge/docs-PDF-d3231c.svg?style=flat-square&logo=adobe&logoColor=white)](https://readthedocs.org/projects/ci-hpc/downloads/pdf/dev/) [![PyPI](https://img.shields.io/pypi/v/cihpc.svg?style=flat-square)](https://pypi.org/project/cihpc/) [![GitHub](https://img.shields.io/github/license/janhybs/ci-hpc.svg?style=flat-square)](https://github.com/janhybs/ci-hpc/blob/master/LICENSE) [![Coveralls github branch](https://img.shields.io/coveralls/github/janhybs/ci-hpc/dev.svg?style=flat-square)](https://coveralls.io/github/janhybs/ci-hpc)

A *simple* framework which can monitor the performance and scalability of software packages.
The framework presented here combines *Continuous Integation* & *High Performance Computing*
together with a minimalistic set of Python scripts.
The results can be visualised in form of static Jupyter notebook or in an interactive web page.


## Features
 - automatically run benchmarks of your project
 - inspect performance and scalability of your project
 - create complex configurations with travis syntax build matrix capabilities
 - use entire computing node with parallel test processing
 - automatically browse a commit history and run the benchmarks
 - automatically determine which tests to run based on results in your database

## Coming soon
 - simplify entire structure with a github push webhook
 - run extra tests when suspecting significant performance change
 - easily create web visualisation configuration from analyzing records in database

## CI-HPC showcase

### Interactive website

- ![Demo site 1](docs/imgs/demo/demo-01.png)
- ![Demo site 2](docs/imgs/demo/demo-03.png)
- ![Demo site 2](docs/imgs/demo/demo-05.png)
- ![Demo site gif](docs/imgs/ci-hpc-demo-dev.gif)


## Documentation & Installation
Read the docs at [ci-hpc.readthedocs.io](https://ci-hpc.readthedocs.io/en/dev/) to know more about installation.
