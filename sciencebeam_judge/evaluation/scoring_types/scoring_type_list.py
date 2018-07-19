from abc import abstractmethod

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

def find_best_match_using_scoring_method(value, other_values, scoring_method):
  best_value = None
  best_score = None
  for other_value in other_values:
    score = get_match_score_obj_for_score_fn(
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

def score_value_as_list_using_scoring_method(
  expected_list, actual_list, scoring_method, include_values=False):

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

def score_value_as_unordered_list_using_scoring_method(
  expected_list, actual_list, scoring_method, include_values=False):

  expected_str = list_to_str(expected_list)
  actual_str = list_to_str(actual_list)
  remaining_list = list(actual_list)
  to_match_score = lambda score: get_match_score_obj_for_score(
    expected_str, actual_str, score, include_values=include_values
  )
  scores = []
  if not expected_list and not actual_list:
    return to_match_score(1.0)
  if len(expected_list) != len(actual_list):
    return to_match_score(0.0)
  for expected_item in expected_list:
    best_value, best_score = find_best_match_using_scoring_method(
      expected_item, remaining_list, scoring_method
    )
    if best_value is not None:
      remaining_list.remove(best_value)
      scores.append(best_score)
    else:
      return to_match_score(0.0)
  return to_match_score(safe_mean(scores))


class ListScoringType(ScoringType):
  @abstractmethod
  def _score_using_scoring_method(
    self, expected_list, actual_list, scoring_method,
    include_values=False, convert_to_lower=False):
    pass

  def score(self, expected, actual, include_values=False, measures=None, convert_to_lower=False):
    expected_list = normalize_list(to_list(expected), convert_to_lower=convert_to_lower)
    actual_list = normalize_list(to_list(actual), convert_to_lower=convert_to_lower)
    scoring_methods = get_scoring_methods(measures=measures)
    scores = {}
    for scoring_method in scoring_methods:
      scores[scoring_method.name] = self._score_using_scoring_method(
        expected_list,
        actual_list,
        scoring_method,
        include_values=include_values,
        convert_to_lower=convert_to_lower
      )
    return scores

class OrderedListScoringType(ListScoringType):
  def _score_using_scoring_method(
    self, expected_list, actual_list, scoring_method,
    include_values=False, convert_to_lower=False):

    return score_value_as_list_using_scoring_method(
      expected_list,
      actual_list,
      scoring_method,
      include_values=include_values
    )

class UnorderedListScoringType(ListScoringType):
  def _score_using_scoring_method(
    self, expected_list, actual_list, scoring_method,
    include_values=False, convert_to_lower=False):

    return score_value_as_unordered_list_using_scoring_method(
      expected_list,
      actual_list,
      scoring_method,
      include_values=include_values
    )

class SetScoringType(ListScoringType):
  def _score_using_scoring_method(
    self, expected_list, actual_list, scoring_method,
    include_values=False, convert_to_lower=False):

    return score_value_as_unordered_list_using_scoring_method(
      sorted(set(expected_list)),
      sorted(set(actual_list)),
      scoring_method,
      include_values=include_values
    )

ORDERED_LIST_SCORING_TYPE = OrderedListScoringType()
UNORDERED_LIST_SCORING_TYPE = UnorderedListScoringType()
SET_SCORING_TYPE = SetScoringType()
