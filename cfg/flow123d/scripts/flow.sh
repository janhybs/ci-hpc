# execute flow in serial for specific yaml file and mesh size
# results will be stored in a temp folder with unique ID, so they can be link
flow123d/bin/flow123d \
    -i <mesh> \
    -o <tmp>/<project-name>/<__unique__> \
    bench_data/benchmarks/<test>/<benchmark>