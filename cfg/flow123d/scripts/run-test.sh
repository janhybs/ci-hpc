echo "BENCHMARK: <benchmark>, INPUT-DIR: <mesh>, CPU: <cpu>"
python3 flow123d/bin/python/runtest.py \
    bench_data/benchmarks/<benchmark>/ \
    --cpu <cpu>                        \
    --status-file                      \
    --no-clean                         \
    --no-compare                       \
    --random-output-dir <__unique__>   \
    -a -- --input_dir <mesh> &

pid=$!
while kill -0 "$pid"; do
  sleep 1
done
