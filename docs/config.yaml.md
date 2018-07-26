# config.yaml specification

## Terminilogy
  - `section`
  
    By a section we understand either `testing` or `installing` section. A section is a main configuration block which groups together installation or benchmark testing procedures. A `section` can contain zero or more `steps`. 
 
    *Note:* Testing section named `install` should contain a configuration for the project installation, compilation or even git cloning.
    Testing section called `test` contains configuration for the benchmark testing.
    
  - `step`
    
    A step is main unit which can contain `shell` commands, git cloning and more.
    
  - `shell`
    
    A shell part can contain `bash` commands (multine line string)
    

## config.yaml example
```yaml
# start of a install section
install:
  
  # first step in install section
  - name: repository-checkout
    git: 
      - url: git@github.com:janhybs/bench-stat.git
      
    # you can also omit shell if there is no need for it
    shell: |
      echo "By this point, the repository is already cloned"
      echo "And checkout out to latest commit"
      
  # seconds step in install section
  - name: compilation-phase
    shell: |
      cd bench-stat
      ./configure --prefix=$(pwd)/build
      make && make install
      
# start of a test section
test:
  # first step in test section
  - name: testing-phase
    shell: |
      cd bench-stat
      build/O3.out
```


## config.yaml structure
```yaml
install:                      # value is list of steps
  - name: string              # name of the step
  
    [description]: string     # description of the step
    
    [enabled]: boolean        # default true, if true step is enabled 
                              # will be processed, otherwised will be skipped
                              
    [verbose]: boolean        # default false, if true shell is 
                              # started with set-x
    
    [repeat]: int             # default 1, number of this step repetition
                              # (useful for benchmark testing)
    
    [shell]: string           # bash commands to be executed
                              
    [output]: string          # default log+stdout, how should be output 
                              # of the shell be displayed, possible values:
                              #   log         - logging to log file only
                              #   stdout      - only display output
                              #   log+stdout  - combination of both
    
    [container]: string       # if set, will execute shell in side container 
                              # value must command(s) which when called will
                              # start container (docker/singularity), command
                              # must contain string %s at the end
                              # %s will be subsituted with a suitable command
                              # 
                              # examples:
                              #   container: |
                              #     docker run --rm -v $(pwd):$(pwd) -w $(pwd) ubuntu %s
                              #   container: |
                              #     module load singularity
                              #     singularity exec -B /mnt sin.simg %s
    [measure]:                # complex type, if set, will measure shell runtime
                              # TODO extend description
    [collect]:                # complex type, if set, will collect results
                              # TODO extend description
    [variables]:              # complex type, if set, will create build matrix of variables
                              # TODO extend description
```
*Note:* keys in `[brackets]` are optional.
