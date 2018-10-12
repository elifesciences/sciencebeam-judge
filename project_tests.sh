#!/bin/bash
set -e

pip install -r requirements.dev.txt

pytest sciencebeam_judge

echo "running pylint"
pylint sciencebeam_judge setup.py

echo "running flake8"
flake8 sciencebeam_judge setup.py

echo "done"
