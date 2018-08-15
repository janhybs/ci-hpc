#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

# install 
pip3 install -r $DIR/requirements.txt "$@"
