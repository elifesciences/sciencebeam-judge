#!/bin/bash
set -e

python -m pytest

echo "running pylint"
pylint sciencebeam_judge tests setup.py

echo "running flake8"
flake8 sciencebeam_judge tests setup.py

echo "done"
