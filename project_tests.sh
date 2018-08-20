#!/bin/bash
set -e

pip install pytest nose && pytest sciencebeam_judge
