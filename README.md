# ScienceBeam Judge

[![Build Status](https://travis-ci.org/elifesciences/sciencebeam-judge.svg?branch=develop)](https://travis-ci.org/elifesciences/sciencebeam-judge)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Pre-requistes

- Python 2.7 ([currently Apache Beam doesn't support Python 3](https://issues.apache.org/jira/browse/BEAM-1373))
- [Apache Beam](https://beam.apache.org/get-started/quickstart-py/)
- [ScienceBeam Gym](https://github.com/elifesciences/sciencebeam-gym) project installed (e.g. by running `pip install -e .` after cloning it)

## Setup

```bash
pip install -r requirements.txt
```

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

For example:

```bash
./evaluate.sh \
  --target-file-list /path/to/data/file-list-validation.tsv \
  --target-file-column=xml_url \
  --prediction-file-list /path/to/data/file-list-validation-prediction.tsv \
  --output-path /path/to/evaluation-results \
  --limit=100
```

Or running it in the cloud with a single worker:

```bash
./evaluate.sh \
  --target-file-list gs://my-bucket/data/file-list-validation.tsv \
  --target-file-column=xml_url \
  --prediction-file-list gs://my-bucket/data/file-list-validation-prediction.tsv \
  --output-path gs://my-bucket/evaluation-results \
  --limit=1000 --cloud --num_workers=1
```

The ouput path will contain the following files:

- `results-*.csv`: The detailed evaluation of every field
- `summary-*.csv`: The overall evaluation
- `grobid-formatted-summary-*.txt`: The summary formatted à la GROBID (see below)

Note: while the _accuracy_ is included, it it is not a good measure for comparison. Use the calculated _f1_ score instead.

## GROBID Like Evaluation

This evaluation is replicating closely the GROBID's [End-to-end evaluation](http://grobid.readthedocs.io/en/latest/End-to-end-evaluation/) and it's [results](https://github.com/kermitt2/grobid/tree/master/grobid-trainer/doc).

It is provided as a reference evaluation.

```bash
./grobid-evaluate-directory.sh --data-path <data path> --target-suffix=<file suffix> --prediction-suffix=<file suffix>
```

For example:

```bash
./grobid-evaluate-directory.sh --data-path PMC_sample_1943 --target-suffix=.nxml --prediction-suffix=.tei-header.xml
```

This command is not cloud ready. Use the `evaluate.sh` command instead, which will generate the GROBID output as well.
