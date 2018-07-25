## Configuring project on HPC server
*Note:* Assuming we are testing project named `hello-world`.
  1. Login to HPC server and clone `ci-hpc` repository:
  ```shell
  cd $WORKSPACE # directory where you keep your projects
  git clone https://github.com/janhybs/ci-hpc.git
  ```
  2. Create configuration `config.yaml` file teh project
  ```shell
  export PROJECT_NAME=hello-world

  mkdir -p ci-hpc/cfg/$PROJECT_NAME
  nano ci-hpc/cfg/$PROJECT_NAME/config.yaml
  ```
  3. Setup `config.yaml` configuration file 

  *Please refer to [config.yaml](doc/config.yaml) section to find out more
  about configuration.*
