cd bench-stat

echo "Running test <test.name> (id=<test.id>)"

# usage:
#   benchmarks/O3.out [json-output-path] [test-id]


# To get reasonable looking output file name we use <__project__> placeholder
#   1) one option is to use date and some random string to avoid collision
#      unique_name=<__project__.current.datetime>-<__project__.current.random>
#
#   2) another option is to simply count
#      unique_name=<__project__.counter.next-05d>
#         the placeholder above is still processed 
#         meaning the counter will be increased by 2 :)

# counter will count (also unique)
unique_name=<__project__.counter.next-05d>
# __unique__ will return unique value for the current run
unique_dir=arts/<__unique__>

mkdir -p $unique_dir
benchmarks/O3.out $unique_dir/result-$unique_name.json <test.id>
