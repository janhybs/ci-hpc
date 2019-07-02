cd flow123d
VERSION=$(bin/flow123d --version 2>&1)
echo "Flow123d installed version: $VERSION"
echo "Required version <git.commit_short>"

if [[ $VERSION == *"<git.commit_short>"* ]]; then
    exit 0
else
    exit 1
fi