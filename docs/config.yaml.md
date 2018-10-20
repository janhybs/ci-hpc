# config.yaml specification

## Terminology
  - `section`
  
    By a section we understand either `testing` or `installing` section. A section is a main configuration block which groups together installation or benchmark testing procedures. A `section` can contain zero or more `steps`. 
 
    *Note:* Testing section named `install` should contain a configuration for the project installation, compilation or even git cloning.
    Testing section called `test` contains configuration for the benchmark testing.
    
  - `step`
    
    A step is main unit which can contain `shell` commands, git cloning and more.
    
  - `shell`
    
    A shell part can contain `bash` commands (multiline line string)
    

## config.yaml example
```yaml
# start of a install section
install:
  
  # first step in the install section
  - name: repository-checkout
    git: 
      - url: git@github.com:janhybs/bench-stat.git
      
    # you can also omit shell if there is no need for it
    shell: |
      echo "By this point, the repository is already cloned"
      echo "And checkout out to latest commit"
      
  # seconds step in the install section
  - name: compilation-phase
    shell: |
      cd bench-stat
      ./configure --prefix=$(pwd)/build
      make && make install
      
# start of a test section
test:
  # first step in the test section
  - name: testing-phase
    shell: |
      cd bench-stat
      build/O3.out
```


## config.yaml structure
*Note:* keys in `[brackets]` are optional.

```yaml
install:                      # value is list of steps
  - name: string              # name of the step
  
    [description]: string     # description of the step
    
    [enabled]: boolean        # default true, if true step is enabled 
                              # will be processed, otherwised will be skipped
                              
    [verbose]: boolean        # default false, if true shell is started with set-x
    
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
                              
    [variables]:              # complex type, if set, will create build matrix of variables
                              # detailed explanation below
                              
    [collect]:                # complex type, if set, will collect results
                              # detailed explanation below
```


### config.yaml `variables` specification

This field will allow you to create so called `build matrix` of all possible combinations of the given 
variables. It is especially useful when running multiple benchmarks which are basically the same
and only thing which is different are arguments passed to the binary. It this case there is no need
to copy the `step` in the install section over and over again only to change a single word in `shell`.
The principle is the same as the `build matrix` used in a
[`.travis.yml`](https://docs.travis-ci.com/user/customizing-the-build/#build-matrix)

You can specify this fields and you can set unlimited amount of variables and their values like this:
```yaml
  variables: 
    - matrix:
        - var-name: [value-1, value-2, value-3]
        - foobar:   [1, 2, 3, 4]
        - test:     [cache, io]
```

The exmaple above will expand to 24 (`3 * 4 * 2`) individual configurations, variables are available
in the `shell` field (and in the `extra` field of a `collect` field).

A shell `field` can use these variables with help of placeholders which are in `<variable>` form,
usage like this:
```yaml
    shell: |
      echo "Running test <test> with arguments foobar=<foobar> and var-name=<var-name>"
      
      # the first echo will look like this:
      # Running test cache with arguments foobar=1 and var-name=value-1
      
      benchmark/O3.out <test> --foobar=<foobar> -v <var-name>
      # the first call of the binary benchmark/O3.out will look like this:
      # benchmark/O3.out cache --foobar=1 -v value-1
```

The value of the variable in a `matrix` field must be an array. It can be array of strings, ints,
floats, or even **dictionaries**. The example below will demonstrate usage of dictionaries.

```yaml
  variables: 
    - matrix:
        - foobar:
            - foo:  10.65   # the first value
              bar:  -3.14
            - foo:   1.05   # the second value
              bar:  42.00
        - test: [cache, io]
```

and usage in shell:
```yaml
    shell: |
      echo "Running test <test> with arguments foo=<foobar.foo> and bar=<foobar.bar>"
      
      # the first echo will look like this:
      # Running test cache with arguments foo=10.65 and bar=-3.14"
      
      benchmark/O3.out <test> --foo=<foobar> --bar=<var-name>
      # the first call of the binary benchmark/O3.out will look like this:
      # benchmark/O3.out cache --foo=10.65 --bar=-3.14
```

There can be multiple `matrix` fields as well (for when you don't want all the combinations):

```yaml
variables:
  - matrix:
    - benchmark: 01_square_regular_grid
    - mesh:
      - 1_15662_el
      - 2_31498_el
      - 4_62302_el
      - 8_124498_el
  - matrix:
    - benchmark: 02_cube_123d
    - mesh:
      - 1_15786_el
      - 2_29365_el
      - 3_47367_el
      - 4_58803_el
```

### config.yaml `collect` specification

If you specify `collect` in a step of the install section, CI-HPC framework will automatically 
look for the benchmark results in form of `json` or `yaml` files. But you have to tell CI-HPC,
what these files are, and how to work with them.

```yaml
collect:
  # value  must be a string containing a path specification.
  # pathname can be either absolute (like /foo/bar/result.json) or 
  # relative (like bar/*/*.json), and can contain shell-style wildcards
  # double asterisk ** will match any files and zero or
  # more directories and subdirectories
  # the value is usually something like
  # directory/*.json
  # more here https://docs.python.org/3.6/library/glob.html
  files: string

  # path to the repository from which git information is taken
  # if set will determine commit, branch and datetime of the current HEAD
  repo: string
  
  # a path to the python module which will take care of the parsing and
  # storing. There is a generic module which does a decent job, so if
  # your result output format can be easily edited, it will work just fine
  [module]: string

  # location where matched files can be moved to after the files has
  # been processed. This will simply move the files to a location 
  # so if you have multiple files from single execution with the same name
  # they will be overwritten, to avoid that see 'cut-prefix' below
  # You can avoiding processing the same results twice.
  # (it is recommended to put the files away)
  [move-to]: string

  # if move-to is set, will cut the path prefix of your files
  # it is especially useful when your results are located deep structure
  # or if they are in a structure, you want to preserve
  [cut-prefix]: string

  # after the processing is done, you can add some extra properties on top
  # you can even use variables from build matrix.
  # for example:
  #     extra:
  #       foo: true
  #       size: <test-size|i>
  # will put extra two fields to a document,
  # which is headed to the database
  # they will be put in a system field:
  #     {
  #       system: {
  #         foo: true,
  #         size: 1024,
  #         ...
  #       },
  #       problem: {
  #         ...
  #       }
  #     }
  # The second variable size will be that of the typo of integer
  # this is bacause |i was specified at the end. All possible 
  # conversions are:
  # |s for string (default)
  # |i for integer
  # |f for floats
  [extra]: dictionary

  # if true, will save the processed results to the DB
  [save-to-db]: boolean
```
