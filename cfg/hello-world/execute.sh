#!/bin/bash --login
NOW=$(date "+%Y-%m-%d_%H-%M-%S")

# print some debug info
echo "[$NOW] running installation script"
echo "#################################################"

# ------------------------------------------------------------------------------
# the following placeholder will be replaced later on
echo "<ci-hpc-exec>"
<ci-hpc-exec>

exit $?
