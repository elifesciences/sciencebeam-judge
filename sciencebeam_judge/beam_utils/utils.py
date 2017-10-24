import logging

import apache_beam as beam

def get_logger():
  return logging.getLogger(__name__)

def MapOrLog(fn):
  def wrapper(x):
    try:
      yield fn(x)
    except Exception as e:
      get_logger().warn('caucht exception (ignoring item): %s, input: %.100s...', e, x)
  return beam.FlatMap(wrapper)
