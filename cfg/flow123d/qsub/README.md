# qsub folder

This folder contains `shell` templates, which specifies how should be `ci-hpc`
started when within `PBS` context (`--pbs` flag). By default if no `--qsub=`
is set, default template will be used, but no modules will be loaded, no env 
variables will be set in this default template script.

It is recommended to create one or more scripts, where modules are properly 
loaded (via `module load` call) and where qsub `resources` are properly 
specified (such as how many cores to use, or how many memory reserve, or even
queue):

## Default file

```sh
#!/bin/bash

echo "<ci-hpc-install>"
<ci-hpc-install>

echo "<ci-hpc-exec>"
<ci-hpc-exec>

exit $?
```

## More complex example

```sh
#!/bin/bash
#PBS -l select=1:ncpus=8:mem=48gb
#PBS -l walltime=01:59:59
#PBS -j oe
#PBS -q charon_2h
#PBS -l place=excl

source /etc/profile
module purge
module load metabase
module load python-3.6.2-gcc
module load python36-modules-gcc
module list -t

echo "<ci-hpc-install>"
<ci-hpc-install>

echo "<ci-hpc-exec>"
<ci-hpc-exec>

exit $?
```

*Note, values `<ci-hpc-exec>` and `<ci-hpc-install>` will be expanded later on*
