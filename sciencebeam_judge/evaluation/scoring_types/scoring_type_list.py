from ..math import safe_mean

from ..normalization import normalize_string

from ..scoring_methods import get_scoring_methods

from ..match_scoring import (
  get_match_score_obj_for_score_fn,
  get_match_score_obj_for_score
)

from .scoring_type import ScoringType

def to_list(x):
  if isinstance(x, str):
    return {x}
  return list(x)

def normalize_list(value, convert_to_lower=False):
  return [
    normalize_string(x, convert_to_lower=convert_to_lower) for x in value
  ]

def list_to_str(x):
  return ', '.join(x)

def score_value_as_list_using_scoring_method(
  expected, actual, scoring_method, include_values=False, convert_to_lower=False):

  expected_list = normalize_list(to_list(expected), convert_to_lower=convert_to_lower)
  actual_list = normalize_list(to_list(actual), convert_to_lower=convert_to_lower)
  expected_str = list_to_str(expected_list)
  actual_str = list_to_str(actual_list)
  to_match_score = lambda score: get_match_score_obj_for_score(
    expected_str, actual_str, score, include_values=include_values
  )

  if not expected_list and not actual_list:
    return to_match_score(1.0)
  if len(expected_list) != len(actual_list):
    return to_match_score(0.0)
  scores = []
  for expected_item, actual_item in zip(expected_list, actual_list):
    score = get_match_score_obj_for_score_fn(
      expected_item,
      actual_item,
      scoring_method.scoring_fn,
      scoring_method.threshold,
      include_values=False
    )['score']

    if score < scoring_method.threshold:
      return to_match_score(0.0)

    scores.append(score)

  return to_match_score(safe_mean(scores))

class ListScoringType(ScoringType):
  def score(self, expected, actual, include_values=False, measures=None, convert_to_lower=False):
    scoring_methods = get_scoring_methods(measures=measures)
    scores = {}
    for scoring_method in scoring_methods:
      scores[scoring_method.name] = score_value_as_list_using_scoring_method(
        expected,
        actual,
        scoring_method,
        include_values=include_values,
        convert_to_lower=convert_to_lower
      )
    return scores

LIST_SCORING_TYPE = ListScoringType()
