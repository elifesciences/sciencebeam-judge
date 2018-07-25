from .scoring_type_list import (
  ORDERED_LIST_SCORING_TYPE,
  UNORDERED_LIST_SCORING_TYPE,
  SET_SCORING_TYPE
)
from .scoring_type_string import STRING_SCORING_TYPE


class ScoringTypeNames(object):
  STRING = 'string'
  LIST = 'list'
  ULIST = 'ulist'
  SET = 'set'

DEFAULT_SCORING_TYPE_NAME = ScoringTypeNames.STRING

SCORING_TYPE_MAP = {
  'str': STRING_SCORING_TYPE,
  ScoringTypeNames.STRING: STRING_SCORING_TYPE,
  ScoringTypeNames.LIST: ORDERED_LIST_SCORING_TYPE,
  ScoringTypeNames.ULIST: UNORDERED_LIST_SCORING_TYPE,
  ScoringTypeNames.SET: SET_SCORING_TYPE
}

def resolve_scoring_type(scoring_type_str):
  try:
    return SCORING_TYPE_MAP[scoring_type_str or DEFAULT_SCORING_TYPE_NAME]
  except KeyError:
    raise ValueError('unrecognised scoring type: %s' % scoring_type_str)
