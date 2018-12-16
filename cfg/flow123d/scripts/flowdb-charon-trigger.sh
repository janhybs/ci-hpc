#!/bin/bash

# args are following
echo "$@"
REPO=$1
COMMIT=$2
BRANCH=$3
GITURL=$4

echo "repo: $REPO, commit: $COMMIT, branch: $BRANCH, url: $GITURL"

REMOTE_PYTHON=/software/python-3.6.2/gcc/bin/python3
REMOTE=/storage/liberec3-tul/home/jan-hybs/projects/ci-hpc
TMPDIR=/storage/liberec3-tul/home/jan-hybs/projects/ci-hpc-projects/.tmp
CLONEDIR=$TMPDIR/$REPO
CFGDIR=$CLONEDIR/config/cihpc

env

# renew kerberos tickets
kinit -k -t /root/jh.keytab jan-hybs@META

# clone the repo
echo ssh -t jan-hybs@charon.metacentrum.cz "rm -rf $CLONEDIR ; git clone $GITURL $CLONEDIR"
ssh -t jan-hybs@charon.metacentrum.cz "rm -rf $CLONEDIR ; git clone $GITURL $CLONEDIR"

# call ci-hpc
echo ssh -t jan-hybs@charon.metacentrum.cz CIHPC_SECRET=$REMOTE/secret.yaml "cd $REMOTE ; $REMOTE_PYTHON bin/cihpc -c $CFGDIR --commit $COMMIT --branch $BRANCH"
ssh -t jan-hybs@charon.metacentrum.cz CIHPC_SECRET=$REMOTE/secret.yaml "cd $REMOTE ; $REMOTE_PYTHON bin/cihpc -c $CFGDIR --commit $COMMIT --branch $BRANCH"
