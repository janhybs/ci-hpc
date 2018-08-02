#!/bin/bash

ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"

cd $ROOT
export PYTHONPATH=$ROOT/ci-hpc:$PYTHONPATH
python3 $ROOT/ci-hpc/visualisation/main.py ${1:-no-debug}
