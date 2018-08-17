#!/bin/bash
set -e

venv/bin/pip install pytest nose && venv/bin/pytest sciencebeam_judge
