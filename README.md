# Pre-requistes

- Python 2.7 ([currently Apache Beam doesn't support Python 3](https://issues.apache.org/jira/browse/BEAM-1373))
- [Apache Beam](https://beam.apache.org/get-started/quickstart-py/)

# Setup

```bash
pip install -r requirements.txt
```

# Evaluation to CSV

```bash
./evaluate-directory.sh --data-path=<data path> [--output-path=<output path] [--target-suffix=<file suffix>] [--prediction-suffix=<file suffix>] [--cloud] [--num_workers=<number of workers>]
```

By default the output path will be _data-path_ + `-results`.

For example:

```bash
./evaluate.sh --data-path PMC_sample_1943 --target-suffix=.nxml --prediction-suffix=.tei-header.xml
```

Or running it in the cloud with a single worker:

```bash
./evaluate.sh --data-path gs://your-bucket/PMC_sample_1943 --target-suffix=.nxml --prediction-suffix=.tei-header.xml --cloud --num_workers=1
```

The ouput path will contain the following files:

* `results-*.csv`: The detailed evaluation of every field
* `summary-*.csv`: The overall evaluation
* `grobid-formatted-summary-*.txt`: The summary formatted à la GROBID (see below)

Note: while the _accuracy_ is included, it it is not a good measure for comparison. Use the calculated _f1_ score instead.


# GROBID Like Evaluation

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
