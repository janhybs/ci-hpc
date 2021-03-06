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
CFGDIR=$REMOTE/cfg/flow123d

SERVER=jan-hybs@charon.metacentrum.cz

env
set -x
# renew kerberos tickets
kinit -k -t /root/jh.keytab jan-hybs@META

# clone the repo and points it to a correct commit under the correct name
echo ssh -t $SERVER "rm -rf $CLONEDIR ; git clone $GITURL $CLONEDIR ; cd $CLONEDIR ; git checkout $COMMIT ; git branch -D $BRANCH || true ; git checkout -b $BRANCH $COMMIT"

# call ci-hpc
echo ssh -t $SERVER CIHPC_SECRET=$REMOTE/secret.yaml "cd $REMOTE ; $REMOTE_PYTHON bin/cihpc -c $CFGDIR --commit $COMMIT --branch $BRANCH"

