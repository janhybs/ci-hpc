## Configuring project on HPC server
*Note:* Assuming we are testing project named `hello-world`.

1. Login to HPC server and clone `ci-hpc` repository:
```shell
cd $WORKSPACE # directory where you keep your projects
git clone https://github.com/janhybs/ci-hpc.git
cd `ci-hpc`
```

2. Install necessary pip packages:
  
   Execute `install.sh` script located in the `bin` folder.
   It is basically shortcut for a `pip3 install -r requirements.txt`. You
   can also pass any arguments to the pip.
   **It is expected to have `python3` and `pip3` in the path.**
   ```bash
   bin/install.sh --user --upgrade
   ```
   To install packages system wide, do not add the `--user ` flag:
   ```bash
   bin/install.sh --upgrade
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

[« back to docs](README.md)
