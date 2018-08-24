from .list import (
  ORDERED_LIST_SCORING_TYPE,
  PARTIAL_ORDERED_LIST_SCORING_TYPE,
  UNORDERED_LIST_SCORING_TYPE,
  PARTIAL_UNORDERED_LIST_SCORING_TYPE,
  SET_SCORING_TYPE,
  PARTIAL_SET_SCORING_TYPE
)
from .string import STRING_SCORING_TYPE
from .table import (
  ORDERED_TABLE_SCORING_TYPE,
  PARTIAL_ORDERED_TABLE_SCORING_TYPE
)


class ScoringTypeNames(object):
  STRING = 'string'
  LIST = 'list'
  PARIAL_LIST = 'partial_list'
  ULIST = 'ulist'
  PARIAL_ULIST = 'partial_ulist'
  SET = 'set'
  PARIAL_SET = 'partial_set'
  TABLE = 'table'
  PARTIAL_TABLE = 'partial_table'

DEFAULT_SCORING_TYPE_NAME = ScoringTypeNames.STRING

SCORING_TYPE_MAP = {
  'str': STRING_SCORING_TYPE,
  ScoringTypeNames.STRING: STRING_SCORING_TYPE,
  ScoringTypeNames.LIST: ORDERED_LIST_SCORING_TYPE,
  ScoringTypeNames.PARIAL_LIST: PARTIAL_ORDERED_LIST_SCORING_TYPE,
  ScoringTypeNames.ULIST: UNORDERED_LIST_SCORING_TYPE,
  ScoringTypeNames.PARIAL_ULIST: PARTIAL_UNORDERED_LIST_SCORING_TYPE,
  ScoringTypeNames.SET: SET_SCORING_TYPE,
  ScoringTypeNames.PARIAL_SET: PARTIAL_SET_SCORING_TYPE,
  ScoringTypeNames.TABLE: ORDERED_TABLE_SCORING_TYPE,
  ScoringTypeNames.PARTIAL_TABLE: PARTIAL_ORDERED_TABLE_SCORING_TYPE
}

def resolve_scoring_type(scoring_type_str):
  try:
    return SCORING_TYPE_MAP[scoring_type_str or DEFAULT_SCORING_TYPE_NAME]
  except KeyError:
    raise ValueError('unrecognised scoring type: %s' % scoring_type_str)
