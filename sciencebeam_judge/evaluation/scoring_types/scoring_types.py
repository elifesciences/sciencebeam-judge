from .scoring_type_list import LIST_SCORING_TYPE
from .scoring_type_set import SET_SCORING_TYPE
from .scoring_type_string import STRING_SCORING_TYPE

class ScoringTypes(object):
  STRING = STRING_SCORING_TYPE
  LIST = LIST_SCORING_TYPE
  SET = SET_SCORING_TYPE

SCORING_TYPE_MAP = {
  'str': ScoringTypes.STRING,
  'string': ScoringTypes.STRING,
  'list': ScoringTypes.LIST,
  'set': ScoringTypes.SET
}

def resolve_scoring_type(scoring_type_str):
  try:
    return SCORING_TYPE_MAP[scoring_type_str or 'str']
  except KeyError:
    raise ValueError('unrecognised scoring type: %s' % scoring_type_str)
