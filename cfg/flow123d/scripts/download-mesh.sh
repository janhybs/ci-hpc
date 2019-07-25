# values will be substitued
server=<server>
filename=<filename>
# determine full name and the dir name
filepath=bench_data/benchmarks/$filename
filedir=$(dirname $filepath)

# download if no such file exists
if [[ ! -f $filepath ]]; then
  wget $server/$filename --progress=bar:force -P $filedir
else
  echo "no need to download file, file $server/$filename already exists"
fi
