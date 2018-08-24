from __future__ import division

import logging
from functools import partial

from sciencebeam_gym.alignment.align import LocalSequenceMatcher, SimpleScoring

from ..normalization import normalize_string

from ..scoring_methods import ScoringMethod, ScoringMethodNames


LOGGER = logging.getLogger(__name__)


DEFAULT_SCORING = SimpleScoring(
  match_score=2,
  mismatch_score=-1,
  gap_score=-2
)


def is_items_value(value):
  try:
    return value.get('items') is not None
  except AttributeError:
    return False


def is_items_list(value_list):
  return value_list and is_items_value(value_list[0])


def normalize_items_list(items_list, convert_to_lower=False):
  return [
    [normalize_string(item, convert_to_lower=convert_to_lower) for item in d['items']]
    for d in items_list
  ]


def _get_exact_matched_characters(haystack_str, needles):
  if not haystack_str:
    return []
  haystack_matched = [False] * len(haystack_str)
  for needle in needles:
    i = haystack_str.find(needle)
    if i >= 0:
      haystack_matched[i:i + len(needle)] = [True] * len(needle)
  return haystack_matched


def _get_fuzzy_matched_characters(haystack_str, needles, threshold):
  if not haystack_str:
    return []
  haystack_matched = [False] * len(haystack_str)
  for needle in needles:
    if not needle:
      continue
    sm = LocalSequenceMatcher(haystack_str, needle, DEFAULT_SCORING)
    mb = sm.get_matching_blocks()
    match_count = sum(size for _, _, size in mb)
    match_ratio = match_count / len(needle)
    LOGGER.debug('match_count=%d, match_ratio=%s, needle=%s', match_count, match_ratio, needle)
    if match_ratio < threshold:
      continue
    for ai, _, size in mb:
      haystack_matched[ai:ai + size] = [True] * size
  return haystack_matched


def _score_items_to(haystack, needles, get_matched_characters_fn):
  LOGGER.debug(
    '_score_items_to: haystack=%s, needles=%s',
    haystack, needles
  )
  haystack = [s for s in haystack if s]
  needles = [s for s in needles if s]
  if not haystack and not needles:
    return 1.0
  if not haystack or not needles:
    return 0.0
  haystack_str = ' '.join(haystack)
  haystack_ignore = [False] * len(haystack_str)
  i = 0
  for item in haystack[:-1]:
    haystack_ignore[len(item)] = True
    i += len(item) + 1
  haystack_matched = get_matched_characters_fn(haystack_str, needles)
  num_matched = sum(
    1 if matched and not ignore else 0
    for matched, ignore in zip(haystack_matched, haystack_ignore)
  )
  num_to_match = sum(1 if not ignore else 0 for ignore in haystack_ignore)
  score = num_matched / num_to_match
  LOGGER.debug(
    '_score_items_to: num_matched=%s, num_to_match=%s, score=%s, haystack_matched=%s',
    num_matched, num_to_match, score, haystack_matched
  )
  return score


def _score_items_exact_to(haystack, needles):
  return _score_items_to(haystack, needles, _get_exact_matched_characters)


def _score_items_fuzzy_to(haystack, needles, threshold):
  return _score_items_to(
    haystack, needles, partial(_get_fuzzy_matched_characters, threshold=threshold)
  )


def get_score_items_to_fn_for_scoring_method(scoring_method):
  if scoring_method.name == ScoringMethodNames.EXACT:
    return _score_items_exact_to
  if scoring_method.name == ScoringMethodNames.LEVENSHTEIN:
    return partial(_score_items_fuzzy_to, threshold=scoring_method.threshold)
  LOGGER.debug('scoring method (%s) has no equivalent item matcher', scoring_method.name)
  return None


def _score_items(expected_items, actual_items, scoring_method):
  LOGGER.debug(
    '_score_items: expected=%s, actual=%s, scoring_method=%s',
    expected_items, actual_items, scoring_method
  )

  score_items_to_fn = get_score_items_to_fn_for_scoring_method(scoring_method)
  if not score_items_to_fn:
    return None

  if len(expected_items) >= len(actual_items):
    return score_items_to_fn(
      actual_items, expected_items
    )
  else:
    return score_items_to_fn(
      expected_items, actual_items
    )


def wrap_items_scoring_method(scoring_method):
  return ScoringMethod(
    scoring_method.name,
    partial(_score_items, scoring_method=scoring_method),
    threshold=scoring_method.threshold
  )


def wrap_items_scoring_methods(scoring_methods):
  return [
    wrap_items_scoring_method(scoring_method)
    for scoring_method in scoring_methods
    if get_score_items_to_fn_for_scoring_method(scoring_method)
  ]
