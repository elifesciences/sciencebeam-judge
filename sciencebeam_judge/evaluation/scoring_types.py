from .math import safe_mean

from .normalization import (
  normalize_whitespace,
  normalize_string
)

from .scoring_methods import (
  get_scoring_methods
)

from .match_scoring import (
  score_obj,
  get_score_obj_for_score
)

def score_list(expected, actual, include_values=False, measures=None, convert_to_lower=False):
  # sep = '\n'
  sep = ''
  expected_str = normalize_whitespace(sep.join(expected))
  actual_str = normalize_whitespace(sep.join(actual))
  if convert_to_lower:
    expected_str = expected_str.lower()
    actual_str = actual_str.lower()
  scores = {}
  scoring_methods = get_scoring_methods(measures=measures)
  for scoring_method in scoring_methods:
    scores[scoring_method.name] = score_obj(
      scoring_method.preprocessing_fn(expected_str),
      scoring_method.preprocessing_fn(actual_str),
      scoring_method.scoring_fn,
      threshold=scoring_method.threshold,
      include_values=include_values
    )
  if not scores:
    raise AttributeError('no measures calculated')
  return scores

def find_best_match_using_scoring_method(value, other_values, scoring_method):
  best_value = None
  best_score = None
  for other_value in other_values:
    score = score_obj(
      value,
      other_value,
      scoring_method.scoring_fn,
      scoring_method.threshold,
      include_values=False
    )['score']
    if score == 1.0:
      return other_value, score
    if best_score is None or score > best_score:
      best_value = other_value
      best_score = score

  if best_score is not None and best_score >= scoring_method.threshold:
    return best_value, best_score
  return None, None

def to_set(x):
  if isinstance(x, str):
    return {x}
  return set(x)

def normalize_set(value, convert_to_lower=False):
  return {
    normalize_string(x, convert_to_lower=convert_to_lower) for x in value
  }

def set_to_str(x):
  return ', '.join(sorted(x))

def score_value_as_set_using_scoring_method(
  expected, actual, scoring_method, include_values=False, convert_to_lower=False):

  expected_set = normalize_set(to_set(expected), convert_to_lower=convert_to_lower)
  actual_set = normalize_set(to_set(actual), convert_to_lower=convert_to_lower)
  expected_str = set_to_str(expected_set)
  actual_str = set_to_str(actual_set)
  remaining_set = set(actual_set)
  scores = []
  if not expected_set and not actual_set:
    return get_score_obj_for_score(
      expected_str, actual_str, 1.0, include_values=include_values
    )
  for expected_item in expected_set:
    best_value, best_score = find_best_match_using_scoring_method(
      expected_item, remaining_set, scoring_method
    )
    if best_value is not None:
      remaining_set.remove(best_value)
      scores.append(best_score)
    else:
      return get_score_obj_for_score(
        expected_str, actual_str, 0.0, include_values=include_values
      )
  if remaining_set:
    return get_score_obj_for_score(
      expected_str, actual_str, 0.0, include_values=include_values
    )
  return get_score_obj_for_score(
      expected_str, actual_str, safe_mean(scores),
      threshold=0.0, include_values=include_values
    )

def score_field_as_set(expected, actual, include_values=False, measures=None, convert_to_lower=False):
  scoring_methods = get_scoring_methods(measures=measures)
  scores = {}
  for scoring_method in scoring_methods:
    scores[scoring_method.name] = score_value_as_set_using_scoring_method(
      expected,
      actual,
      scoring_method,
      include_values=include_values,
      convert_to_lower=convert_to_lower
    )
  return scores

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

def get_field_scoring_type(scoring_type_by_field_map, field_name):
  if scoring_type_by_field_map is None:
    scoring_type_by_field_map = {}
  return resolve_scoring_type(scoring_type_by_field_map.get(
    field_name,
    scoring_type_by_field_map.get('default')
  ))

def score_field_as_type(
  expected, actual, scoring_type, include_values=False, measures=None, convert_to_lower=False):

  return scoring_type.score(
    expected, actual,
    include_values=include_values,
    measures=measures,
    convert_to_lower=convert_to_lower
  )
