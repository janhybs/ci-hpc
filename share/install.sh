#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"

# install 
if [[ -z "$1" ]]; then
  pip3 install -r $DIR/requirements.txt --upgrade --user
else
  pip3 install -r $DIR/requirements.txt --upgrade
fi
