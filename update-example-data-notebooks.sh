#!/bin/bash

set -e

docker-compose build sciencebeam-judge-jupyter

cwd="$(pwd)"

update_notebook() {
    notebook_file=$1
    docker-compose run --rm \
        sciencebeam-judge-jupyter \
        jupyter nbconvert --to notebook --execute --inplace ./$notebook_file
    stderr_content=$(
        docker-compose run --rm --entrypoint 'sh -c' sciencebeam-judge-jupyter \
        "grep 'stderr' ./$notebook_file" | cat
    )
    if [ ! -z "$stderr_content" ]; then
        echo "Error: Notebook contains stderr output"
        exit 3
    fi
}

update_notebook conversion-results-summary.ipynb
update_notebook conversion-results-details.ipynb
