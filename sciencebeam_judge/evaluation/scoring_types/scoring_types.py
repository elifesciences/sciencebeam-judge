from .scoring_type_list import (
  ORDERED_LIST_SCORING_TYPE,
  UNORDERED_LIST_SCORING_TYPE,
  SET_SCORING_TYPE
)
from .scoring_type_string import STRING_SCORING_TYPE

SCORING_TYPE_MAP = {
  'str': STRING_SCORING_TYPE,
  'string': STRING_SCORING_TYPE,
  'list': ORDERED_LIST_SCORING_TYPE,
  'ulist': UNORDERED_LIST_SCORING_TYPE,
  'set': SET_SCORING_TYPE
}

def resolve_scoring_type(scoring_type_str):
  try:
    return SCORING_TYPE_MAP[scoring_type_str or 'str']
  except KeyError:
    raise ValueError('unrecognised scoring type: %s' % scoring_type_str)
