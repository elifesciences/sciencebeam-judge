from __future__ import division

import logging

import numpy as np

from .scoring_type_set import SET_SCORING_TYPE


LOGGING = logging.getLogger(__name__)

SOME_TEXT = 'test 123'

is_close = lambda a, b: np.allclose([a], [b])

class TestScoreFieldAsSet(object):
  def test_should_match_if_items_match_in_different_order(self):
    result = SET_SCORING_TYPE.score(['a', 'b'], ['b', 'a'])
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 1
    assert result['soft']['score'] == 1
    assert result['levenshtein']['score'] == 1
    assert result['ratcliff_obershelp']['score'] == 1

  def test_should_match_empty_lists(self):
    result = SET_SCORING_TYPE.score([], [])
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 1

  def test_should_not_match_different_values(self):
    result = SET_SCORING_TYPE.score(['a'], ['b'])
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 0

  def test_should_not_match_with_missing_value(self):
    result = SET_SCORING_TYPE.score(['a', 'b'], ['a'])
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 0

  def test_should_not_match_with_extra_value(self):
    result = SET_SCORING_TYPE.score(['a'], ['a', 'b'])
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 0

  def test_should_normalize_space(self):
    result = SET_SCORING_TYPE.score(['a  b'], ['a b'])
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 1

  def test_should_convert_to_lower_if_enabled(self):
    result = SET_SCORING_TYPE.score(['a', 'B'], ['A', 'b'], convert_to_lower=True)
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 1

  def test_should_not_convert_to_lower_if_not_enabled(self):
    result = SET_SCORING_TYPE.score(['a', 'B'], ['A', 'b'], convert_to_lower=False)
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 0
