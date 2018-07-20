#!/bin/bash --login
#PBS -j oe
#PBS -q charon
#PBS -l nodes=1:ncpus=1:mem=2gb
#PBS -l walltime=00:10:00
# # disabled option -l place=excl

module load python-3.6.2-gcc
module load python36-modules-gcc

NOW=$(date "+%Y-%m-%d_%H-%M-%S")

# print some debug info
echo "[$NOW] running installation script"
if [[ -n "$PBS_JOBID" ]]; then
  echo "Running job $PBS_JOBNAME ($PBS_JOBID) in `pwd`"
  echo "Time: `date`"
  echo "Running on master node: `hostname`"
  echo "Using nodefile :         $PBS_NODEFILE"
  cat $PBS_NODEFILE
else
  echo "Running job on frontend in `pwd`"
  echo "Time: `date`"
  echo "Running on master node: `hostname`"
fi
echo "#################################################"

# ------------------------------------------------------------------------------
# the following placeholder will be replaced later on
echo "<ci-hpc-exec>"
<ci-hpc-exec>

exit $?
