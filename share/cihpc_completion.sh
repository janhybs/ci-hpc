#!/bin/bash


if [ -n "$ZSH_VERSION" ]; then
  compdef "_arguments \
                '--project[project name]' \
                '--git-branch[name of the branch]' \
                '--git-commit[commit hash, either short or full hash of the commit]' \
                '--git-url[URL of the repository, (ignore for now)]' \
                '--config-dir[location of the directory containing config.yaml file]' \
                '--execute[either local or pbs value, to start cihpc process]' \
                '*:path:_path_files' \
                ':arg:(install test)' \
                " cihpc
elif [ -n "$BASH_VERSION" ]; then
  DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null && pwd )"
  CFG=$(realpath $DIR/../cfg/)
  dirs=$(find $CFG/* -type d -exec basename {} \;)
  cfg_dirs=
  for p in $dirs; do
    cfg_dirs="$cfg_dirs --config-dir=$p"
  done
  _cihpc () {
      local cur=${COMP_WORDS[COMP_CWORD]}
      local hints="--project --git-branch --git-commit --git-url --execute=local --execute=pbs test install"
      COMPREPLY=( $(compgen -W "$hints $cfg_dirs" -- $cur) )
  }

  complete -F _cihpc cihpc
  complete -F _cihpc ./cihpc
  complete -F _cihpc bin/cihpc
fi

