from .scoring_type_set import score_field_as_set
from .scoring_type_string import score_list

class ScoringType(object):
  def __init__(self, score_field_fn):
    self._score_field_fn = score_field_fn

  def score(self, expected, actual, include_values=False, measures=None, convert_to_lower=False):
    return self._score_field_fn(
      expected, actual, include_values=include_values, measures=measures,
      convert_to_lower=convert_to_lower
    )

class ScoringTypes(object):
  STRING = ScoringType(score_list)
  SET = ScoringType(score_field_as_set)

SCORING_TYPE_MAP = {
  'str': ScoringTypes.STRING,
  'string': ScoringTypes.STRING,
  'set': ScoringTypes.SET
}

def resolve_scoring_type(scoring_type_str):
  try:
    return SCORING_TYPE_MAP[scoring_type_str or 'str']
  except KeyError:
    raise ValueError('unrecognised scoring type: %s' % scoring_type_str)
