#!/bin/bash

set -x
python3 ../ci-hpc/visualisation/main.py ${1:-no-debug}
