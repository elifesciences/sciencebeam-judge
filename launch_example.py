from __future__ import absolute_import
from __future__ import print_function

from sciencebeam_judge.evaluate_pipeline import run

if __name__ == '__main__':
  # from sciencebeam.examples.logging_config import configure_logging

  # configure_logging()
  import logging
  logging.basicConfig(level='INFO')

  try:
    run(argv=[
      "--data-path", "/home/deuser/_git_/elife/pdf-xml/data/PMC_sample_1943-subset"
    ])
  except Exception as e:
    print(e)

  print("done")
