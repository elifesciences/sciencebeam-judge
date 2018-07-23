from six import string_types
from six.moves.configparser import ConfigParser


def parse_config(filename_or_fp):
  config = ConfigParser()
  if isinstance(filename_or_fp, string_types):
    config.read(filename_or_fp)
  else:
    config.readfp(filename_or_fp)
  return config

def config_to_dict(config):
  return {
    k: dict(config.items(k))
    for k in config.sections()
  }

def parse_config_as_dict(filename_or_fp):
  return config_to_dict(parse_config(filename_or_fp))
