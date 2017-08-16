# Pre-requistes

* Python 2 or 3

# Setup

```bash
pip install -r requirements.txt
```

# GROBID Like Evaluation

This evaluation is replicating closely the GROBID's [End-to-end evaluation](http://grobid.readthedocs.io/en/latest/End-to-end-evaluation/).

It is provided as a reference evaluation.

```bash
./grobid-evaluate-directory.sh --data-path <data path> --target-suffix=<file suffix> --prediction-suffix=<file suffix>
```

For example:

```bash
./grobid-evaluate-directory.sh --data-path PMC_sample_1943 --target-suffix=.nxml --prediction-suffix=.tei-header.xml
```
