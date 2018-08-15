#!/bin/bash --login
# this script does not contain any PBS shell lines defining
# resource usage
# they must be specified in the qsub command

#PBS -l select=1:ncpus=8:mem=16gb
#PBS -l walltime=1:00:00
#PBS -j oe
#PBS -q charon
#PBS -l place=excl
# ncpus=72 !!!


# hard path is recommended since script location is elsewhere when in PBS
ROOT=/storage/praha1/home/jan-hybs/projects/ci-hpc
NOW=$(date "+%Y-%m-%d_%H-%M-%S")
cd $ROOT

# print some debug info
echo "#############################################"
echo "[$NOW] running installation script with following args:"
echo "$@"
echo "#############################################"
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
echo "#############################################"


# Example for the HPC charon.nti.tul.cz
# ------------------------------------------------------------------------------

. /etc/profile
module purge
module load metabase
module load python-3.6.2-gcc
module load python36-modules-gcc
module list -t
set -x

# the following line will be replaced later on
<ci-hpc-install>

# the following line will be replaced later on
/usr/bin/time <ci-hpc-exec>

exit $?
