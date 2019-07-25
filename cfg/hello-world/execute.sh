#!/bin/bash --login
#
#PBS -l select=1:ncpus=1:mem=1gb
#PBS -l walltime=00:15:00
#PBS -j oe
#PBS -q charon
# P B S -l place=excl


# hard path is recommended since script location is elsewhere when in PBS
ROOT=/storage/praha1/home/jan-hybs/projects/ci-hpc
NOW=$(date "+%Y-%m-%d_%H-%M-%S")
cd $ROOT

# print some debug info
echo "#############################################"
echo "host: $(hostname)"
echo "time: $(date)"
echo "user: $(whoami) ($(id))"
echo "pwd:  $(pwd)"
echo "[$NOW] running installation script with following args:"
echo "$@"
echo "#############################################"
if [[ -n "$PBS_JOBID" ]]; then
  echo "Running job $PBS_JOBNAME ($PBS_JOBID) "
  echo "Using nodefile :         $PBS_NODEFILE"
  cat $PBS_NODEFILE
  echo "#############################################"
fi


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
<ci-hpc-exec> 2>&1 | tee .pbs.job.log

exit $?
