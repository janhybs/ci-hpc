#!/bin/bash --login
# this script does not contain any PBS shell lines defining
# resource usage
# they must be specified in the qsub command

#PBS -j oe
#PBS -q charon
#PBS -l place=excl
# ncpus=72 !!!

# Example for the HPC charon.nti.tul.cz
# ------------------------------------------------------------------------------
. /etc/profile
module purge
module load metabase
module load python-3.6.2-gcc
module load python36-modules-gcc
module list



# hard path is recommended since script location is elsewhere
ROOT=/storage/liberec1-tul/home/jan-hybs/projects/ci-hpc
cd $ROOT

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
set -x


python3 $ROOT/ci-hpc/main.py test --project=flow123d
exit $?
