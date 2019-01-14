#!/bin/bash

set -e

docker-compose build sciencebeam-judge

cwd="$(pwd)"

update_results() {
    tool=$1
    docker-compose run --rm \
        --volume="$cwd/example-data:/example-data" \
        sciencebeam-judge \
        ./evaluate.sh \
        --target-file-list /example-data/pmc-sample-1943-cc-by-subset/file-list.tsv \
        --target-file-column=xml_url \
        --prediction-file-list /example-data/pmc-sample-1943-cc-by-subset-results/file-list-$tool.lst \
        --output-path /example-data/pmc-sample-1943-cc-by-subset-results/evaluation-results/$tool \
        --sequential
}

update_results cermine
update_results grobid-tei
