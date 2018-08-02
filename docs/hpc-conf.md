## Configuring project on HPC server
*Note:* Assuming we are testing project named `hello-world`.

  1. Login to HPC server and clone `ci-hpc` repository:
  ```shell
  cd $WORKSPACE # directory where you keep your projects
  git clone https://github.com/janhybs/ci-hpc.git
  cd `ci-hpc`
  ```
  
  2. Install necessary pip packages:
    
    Execure `install.sh` script located in the `bin` folder.
    By default it will install the packages for the current user (no root required). 
    **It is expected to have `python3` and `pip3` in the path.**
    ```bash
    bin/install.sh
    ```
    To install packages system wide, add flag `--system`:
    ```bash
    bin/install.sh --system
    ```
    
  3. Create configuration file `config.yaml` for the project
  ```shell
  export PROJECT_NAME=hello-world

  mkdir -p cfg/$PROJECT_NAME
  nano     cfg/$PROJECT_NAME/config.yaml
  ```
  
  4. Setup `config.yaml` configuration file 

  *Please refer to [config.yaml](config.yaml.md) section to find out more
  about configuration.*
