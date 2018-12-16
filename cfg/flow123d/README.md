# CI-HPC configuration

This folder contains several `yaml` configuration files controlling behaviour
of the `ci-hpc` framework.


 - **`config.yaml`**
 
    a main configuration file, which control how is
    the software installed and tested.
    
 - **`variables.yaml`** *
 
    a `yaml` file containing global variables, which will be used in
    in a `config.yaml` file.

 - **`execute.sh`** *
 
    a `shell` template, which specifies how should be `ci-hpc` processing started when within `PBS` context.
 
 - **`www.yaml`**
 
    a `yaml` file which contains configuration for the visualization
    component.

The files mark with * are **optional**.
 
