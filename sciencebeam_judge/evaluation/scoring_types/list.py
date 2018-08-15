import logging
from abc import abstractmethod

from six import text_type

from sciencebeam_gym.utils.collection import extend_dict

from ..math import safe_mean

from ..normalization import normalize_string

from ..scoring_methods import get_scoring_methods

from ..match_scoring import (
  get_match_score_obj_for_score_fn,
  get_match_score_obj_for_score,
  MatchScoringProps
)

from .scoring_type import ScoringType

from .items import wrap_items_scoring_methods, is_items_list, normalize_items_list


LOGGER = logging.getLogger(__name__)


def to_list(x):
  if isinstance(x, str):
    return {x}
  return list(x)


def normalize_list(value, convert_to_lower=False):
  return [
    normalize_string(x, convert_to_lower=convert_to_lower) for x in value
  ]


def list_to_str(l):
  return ', '.join(text_type(x) for x in l)


def pad_list(l, desired_length, pad_value=None):
  if len(l) == desired_length:
    return l
  assert desired_length > len(l)
  return l + [pad_value] * (desired_length - len(l))


def pad_longest(*lists):
  max_len = max(len(l) for l in lists)
  return [pad_list(l, max_len) for l in lists]


def find_best_match_using_scoring_method(value, other_values, scoring_method, include_values=False):
  best_value = None
  best_score = None
  for other_value in other_values:
    score = get_match_score_obj_for_score_fn(
      value,
      other_value,
      scoring_method.scoring_fn,
      scoring_method.threshold,
      include_values=include_values
    )
    if score['score'] == 1.0:
      return other_value, score
    if not best_score or score['score'] > best_score['score']: # pylint: disable=unsubscriptable-object
      best_value = other_value
      best_score = score

  if best_score is not None and best_score['score'] >= scoring_method.threshold:
    return best_value, best_score
  return None, None


def _sum_field(sequence, key):
  return sum(x[key] for x in sequence)


def _combine_partial_match_scores(scores, template_score):
  LOGGER.debug('_combine_partial_match_scores: %s', scores)
  return extend_dict(template_score, {
    MatchScoringProps.TRUE_POSITIVE: _sum_field(scores, MatchScoringProps.TRUE_POSITIVE),
    MatchScoringProps.FALSE_POSITIVE: _sum_field(scores, MatchScoringProps.FALSE_POSITIVE),
    MatchScoringProps.FALSE_NEGATIVE: _sum_field(scores, MatchScoringProps.FALSE_NEGATIVE),
    MatchScoringProps.TRUE_NEGATIVE: _sum_field(scores, MatchScoringProps.TRUE_NEGATIVE),
    MatchScoringProps.SUB_SCORES: scores
  })


def score_value_as_list_using_match_scoring_fn(
  expected_list, actual_list,
  expected_str, actual_str,
  match_scoring_fn, threshold,
  include_values=False, partial=False):

  to_match_score = lambda score: get_match_score_obj_for_score(
    expected_str, actual_str, score,
    threshold=threshold, include_values=include_values
  )

  if partial:
    expected_list, actual_list = pad_longest(expected_list, actual_list)
  else:
    if not expected_list and not actual_list:
      LOGGER.debug('empty lists (expected and actual), 1.0 score')
      return to_match_score(1.0)
    if len(expected_list) != len(actual_list):
      LOGGER.debug(
        'number of items mismatch (expected=%d, actual=%d), 0.0 score',
        len(expected_list), len(actual_list)
      )
      return to_match_score(0.0)
  scores = []
  for expected_item, actual_item in zip(expected_list, actual_list):
    score = match_scoring_fn(
      expected_item,
      actual_item
    )

    if score['score'] < threshold and not partial:
      return to_match_score(0.0)

    scores.append(score)

  LOGGER.debug(
    'score_value_as_list_using_match_scoring_fn, partial=%s, scores=%s', partial, scores
  )
  mean_score = safe_mean([score['score'] for score in scores]) if scores else 1.0
  result_score = to_match_score(mean_score)
  if partial:
    result_score = _combine_partial_match_scores(scores, result_score)
  return result_score


def score_value_as_list_using_scoring_method(
  expected_list, actual_list, scoring_method,
  include_values=False, partial=False):

  expected_str = list_to_str(expected_list)
  actual_str = list_to_str(actual_list)
  return score_value_as_list_using_match_scoring_fn(
    expected_list, actual_list,
    expected_str, actual_str,
    lambda expected_item, actual_item: get_match_score_obj_for_score_fn(
      expected_item or '',
      actual_item or '',
      scoring_method.scoring_fn,
      scoring_method.threshold,
      include_values=include_values
    ),
    scoring_method.threshold,
    include_values=include_values,
    partial=partial
  )


def score_value_as_unordered_list_using_scoring_method(
  expected_list, actual_list, scoring_method,
  include_values=False, partial=False):

  expected_str = list_to_str(expected_list)
  actual_str = list_to_str(actual_list)
  remaining_list = list(actual_list)
  to_match_score = lambda score: get_match_score_obj_for_score(
    expected_str, actual_str, score,
    threshold=scoring_method.threshold, include_values=include_values
  )
  scores = []
  if not partial:
    if not expected_list and not actual_list:
      LOGGER.debug('empty lists (expected and actual), 1.0 score')
      return to_match_score(1.0)
    if len(expected_list) != len(actual_list):
      LOGGER.debug(
        'number of items mismatch (expected=%d, actual=%d), 0.0 score',
        len(expected_list), len(actual_list)
      )
      return to_match_score(0.0)
  for expected_item in expected_list:
    best_value, best_score = find_best_match_using_scoring_method(
      expected_item, remaining_list, scoring_method,
      include_values=include_values
    )
    if best_value is not None:
      LOGGER.debug(
        'found match (%s), adding to list, score=%.3f, expected_item=%s, matching_item=%s',
        scoring_method, best_score['score'], expected_item, best_value
      )
      remaining_list.remove(best_value)
      scores.append(best_score)
    else:
      LOGGER.debug(
        'no match found (%s), 0.0 score, expected_item=%s, remaining_list=%s',
        scoring_method, expected_item, remaining_list
      )
      if partial:
        scores.append(get_match_score_obj_for_score(
          expected_item, '', 0.0,
          threshold=scoring_method.threshold, include_values=include_values
        ))
      else:
        return to_match_score(0.0)
  for remaining_item in remaining_list:
    scores.append(get_match_score_obj_for_score(
      '', remaining_item, 0.0,
      threshold=scoring_method.threshold, include_values=include_values
    ))
  mean_score = safe_mean([score['score'] for score in scores]) if scores else 1.0
  LOGGER.debug(
    'returning list score (%s), mean_score=%.3f, scores=%s',
    scoring_method, mean_score, scores
  )
  result_score = to_match_score(mean_score)
  if partial:
    result_score = _combine_partial_match_scores(scores, result_score)
  return result_score


class ListScoringType(ScoringType):
  def __init__(self, partial=False):
    self.partial = partial

  @abstractmethod
  def _score_using_scoring_method(
    self, expected_list, actual_list, scoring_method,
    include_values=False, convert_to_lower=False):
    pass

  def score_items(self, expected_list, actual_list, include_values=False, measures=None, convert_to_lower=False):
    expected_list = normalize_items_list(expected_list, convert_to_lower=convert_to_lower)
    actual_list = normalize_items_list(actual_list, convert_to_lower=convert_to_lower)
    scoring_methods = wrap_items_scoring_methods(get_scoring_methods(measures=measures))
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

  def score_list(self, expected_list, actual_list, include_values=False, measures=None, convert_to_lower=False):
    expected_list = normalize_list(expected_list, convert_to_lower=convert_to_lower)
    actual_list = normalize_list(actual_list, convert_to_lower=convert_to_lower)
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

  def score(self, expected, actual, **kwargs):
    expected_list = to_list(expected)
    actual_list = to_list(actual)
    if is_items_list(expected_list) or is_items_list(actual_list):
      return self.score_items(expected_list, actual_list, **kwargs)
    else:
      return self.score_list(expected_list, actual_list, **kwargs)


class OrderedListScoringType(ListScoringType):
  def _score_using_scoring_method(
    self, expected_list, actual_list, scoring_method,
    include_values=False, convert_to_lower=False):

    return score_value_as_list_using_scoring_method(
      expected_list,
      actual_list,
      scoring_method,
      include_values=include_values,
      partial=self.partial
    )


class UnorderedListScoringType(ListScoringType):
  def _score_using_scoring_method(
    self, expected_list, actual_list, scoring_method,
    include_values=False, convert_to_lower=False):

    return score_value_as_unordered_list_using_scoring_method(
      expected_list,
      actual_list,
      scoring_method,
      include_values=include_values,
      partial=self.partial
    )


class SetScoringType(ListScoringType):
  def _score_using_scoring_method(
    self, expected_list, actual_list, scoring_method,
    include_values=False, convert_to_lower=False):

    return score_value_as_unordered_list_using_scoring_method(
      sorted(set(expected_list)),
      sorted(set(actual_list)),
      scoring_method,
      include_values=include_values,
      partial=self.partial
    )


ORDERED_LIST_SCORING_TYPE = OrderedListScoringType()
PARTIAL_ORDERED_LIST_SCORING_TYPE = OrderedListScoringType(partial=True)

UNORDERED_LIST_SCORING_TYPE = UnorderedListScoringType()
PARTIAL_UNORDERED_LIST_SCORING_TYPE = UnorderedListScoringType(partial=True)

SET_SCORING_TYPE = SetScoringType()
PARTIAL_SET_SCORING_TYPE = SetScoringType(partial=True)
