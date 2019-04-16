# ScienceBeam Judge

[![Build Status](https://travis-ci.org/elifesciences/sciencebeam-judge.svg?branch=develop)](https://travis-ci.org/elifesciences/sciencebeam-judge)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

This project implements a JATS/TEI conversion [evaluation](docs/evaluation.md). It can be configured to also be handle other similar document types.

## Pre-requistes

- Python 2.7 ([currently Apache Beam doesn't support Python 3](https://issues.apache.org/jira/browse/BEAM-1373))
- [Apache Beam](https://beam.apache.org/get-started/quickstart-py/)

You can install default versions of pre-requisites (apart from Python) using:

```bash
pip install -r requirements.prereq.txt
```

## Setup

```bash
pip install -r requirements.txt
pip install -r requirements.dev.txt
```

## Configuration

The [xml-mapping.conf](xml-mapping.conf) configures how fields should be extracted from the XML.

The [evaluation.conf](evaluation.conf) allows further evaluation details to be configured.

## File Lists

ScienceBeam Judge use file lists to avoid having to pass in file patterns and rules. File lists can be CSVs (`.csv`), TSVs (`.tsv`) or plain text list (`.lst`). Generally lists need to align, so that the target and prediction files correspond.

The following tools may help creating those lists depending on your directory structure.

### With source document and XML files

If you used ScienceBeam for the bulk conversion, then you will likely have already created a file that pairs the source document with the target document.

You can find such a pair using a command similar to the following:

```bash
python -m sciencebeam_utils.tools.find_file_pairs \
    --data-path ./example-data/pmc-sample-1943-cc-by-subset \
    --source-pattern *.pdf.gz \
    --xml-pattern *.nxml.gz \
    --out ./example-data/pmc-sample-1943-cc-by-subset/file-list-example.tsv
```

Note: in this case the above command won't find any pairs because this repository doesn't contain the source document (the PDFs).

### With only XML files

If you are only using ScienceBeam Judge to compare XML files you can create a file lists of the target XML first:

```bash
find ./example-data/pmc-sample-1943-cc-by-subset \
    -name '*.nxml' -printf '%P\n' \
    | sort \
    > ./example-data/pmc-sample-1943-cc-by-subset/file-list-target.lst
```

To then create a file list that matches the source you could run:

```bash
python -m sciencebeam_utils.tools.get_output_files \
    --source-base-path ./example-data/pmc-sample-1943-cc-by-subset \
    --source-file-list file-list-target.lst \
    --output-file-suffix=.xml \
    --output-base-path ./example-data/pmc-sample-1943-cc-by-subset-results/cermine \
    --output-file-list ./example-data/pmc-sample-1943-cc-by-subset-results/cermine/file-list.lst \
    --use-relative-paths
```

This however requires that the filenames also match up and only differ by their suffix.

## Evaluation to CSV

You need to have a file list with the _target xml_ and _prediction xml_ files (both can be in the same file but have different columns or separate files where the lines are aligned to each other). Files can optionally be gzipped with the _.gz_ file extension.

```bash
./evaluate.sh \
  --target-file-list=<path to target file list> \
  [--target-file-column=<column name>] \
  --prediction-file-list=<path to prediction file list> \
  [--prediction-file-column=<column name>] \
  --output-path=<output directory> \
  [--limit=<max file pair count> \
  [--cloud] \
  [--num_workers=<number of workers>]
```

For example to evaluate the provide `example-data` for _cermine_ and _grobid-tei_:

```bash
./evaluate.sh \
  --target-file-list ./example-data/pmc-sample-1943-cc-by-subset/file-list.tsv \
  --target-file-column=xml_url \
  --prediction-file-list ./example-data/pmc-sample-1943-cc-by-subset-results/cermine/file-list.lst \
  --output-path ./example-data/pmc-sample-1943-cc-by-subset-results/cermine/evaluation-results \
  --sequential
```

```bash
./evaluate.sh \
  --target-file-list ./example-data/pmc-sample-1943-cc-by-subset/file-list.tsv \
  --target-file-column=xml_url \
  --prediction-file-list ./example-data/pmc-sample-1943-cc-by-subset-results/grobid-tei/file-list.lst \
  --output-path ./example-data/pmc-sample-1943-cc-by-subset-results/grobid-tei/evaluation-results \
  --sequential
```

(The _--sequential_ flag is added to produce output in the same order)

Or running it in the cloud with a single worker:

```bash
./evaluate.sh \
  --target-file-list gs://my-bucket/data/file-list-validation.tsv \
  --target-file-column=xml_url \
  --prediction-file-list gs://my-bucket/data/file-list-validation-prediction.tsv \
  --output-path gs://my-bucket/evaluation-results \
  --limit=1000 --cloud --num_workers=1
```

The examples data results may also be updated using Docker:

```bash
./update-example-data-results.sh
```

The ouput path will contain the following files:

- `results-*.csv`: The detailed evaluation of every field
- `summary-*.csv`: The overall evaluation
- `grobid-formatted-summary-*.txt`: The summary formatted à la GROBID (see below)

Note: while the _accuracy_ is included, it it is not a good measure for comparison. Use the calculated _f1_ score instead.

## GROBID Like Evaluation

This evaluation is replicating closely the GROBID's [End-to-end evaluation](http://grobid.readthedocs.io/en/latest/End-to-end-evaluation/) and it's [results](https://github.com/kermitt2/grobid/tree/master/grobid-trainer/doc).

It is provided as a reference evaluation.

Use the `evaluate.sh` command, which will generate the GROBID output (in addition to the CSV files).

Note: it will only include scores for the _scoring type_ `string`.

## Notebooks

The [notebooks](./notebooks) can be run via [Jupyter](https://jupyter.org/).

### Using Docker to run Jupyter

Pre-requisites:

- [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/)

```bash
docker-compose up --build sciencebeam-judge-jupyter
```

Open [http://localhost:8890/](http://localhost:8890/).

(The port can be configured using the _SCIENCEBEAM_JUPYTER_PORT_ environment variable)

### Using Local Jupyter installation

Pre-requisites:

- [Jupyter](https://jupyter.org/)

Install the additional dependencies:

```bash
pip install -r requirements.notebook.txt
```
