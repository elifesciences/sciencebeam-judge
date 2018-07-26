from __future__ import division

import logging

from abc import ABCMeta, abstractmethod

from six import with_metaclass

from ..match_scoring import MatchScoringProps

from .scoring_type_list import (
  ORDERED_LIST_SCORING_TYPE,
  UNORDERED_LIST_SCORING_TYPE,
  SET_SCORING_TYPE
)


LOGGING = logging.getLogger(__name__)

SOME_TEXT = 'test 123'

ALMOST_MATCHING_TEXTS = [
  'This almost matches',
  'This almost matched'
]


class _TestCommonListScoringType(object, with_metaclass(ABCMeta)):
  @abstractmethod
  def score(self, *args, **kwargs):
    pass

  def test_should_match_if_items_match_in_same_order(self):
    result = self.score(['a', 'b'], ['a', 'b'])
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 1
    assert result['soft']['score'] == 1
    assert result['levenshtein']['score'] == 1
    assert result['ratcliff_obershelp']['score'] == 1

  def test_should_match_empty_lists(self):
    result = self.score([], [])
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 1

  def test_should_not_match_different_values(self):
    result = self.score(['a'], ['b'])
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 0

  def test_should_not_match_with_missing_value(self):
    result = self.score(['a', 'b'], ['a'])
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 0

  def test_should_not_match_with_extra_value(self):
    result = self.score(['a'], ['a', 'b'])
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 0

  def test_should_normalize_space(self):
    result = self.score(['a  b'], ['a b'])
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 1

  def test_should_convert_to_lower_if_enabled(self):
    result = self.score(['a', 'B'], ['A', 'b'], convert_to_lower=True)
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 1

  def test_should_not_convert_to_lower_if_not_enabled(self):
    result = self.score(['a', 'B'], ['A', 'b'], convert_to_lower=False)
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 0

  def test_should_allow_almost_matching_text(self):
    result = self.score([ALMOST_MATCHING_TEXTS[0]], [ALMOST_MATCHING_TEXTS[1]])
    LOGGING.debug('result: %s', result)
    assert result['exact'][MatchScoringProps.SCORE] == 0
    assert result['exact'][MatchScoringProps.TRUE_POSITIVE] == 0
    assert result['levenshtein'][MatchScoringProps.SCORE] > 0
    assert result['levenshtein'][MatchScoringProps.TRUE_POSITIVE] == 1

class TestOrderedListScoringType(_TestCommonListScoringType):
  def score(self, *args, **kwargs):
    return ORDERED_LIST_SCORING_TYPE.score(*args, **kwargs)

  def test_should_not_match_different_order(self):
    result = self.score(['a', 'b'], ['b', 'a'])
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 0

class TestUnorderedListScoringType(_TestCommonListScoringType):
  def score(self, *args, **kwargs):
    return UNORDERED_LIST_SCORING_TYPE.score(*args, **kwargs)

  def test_should_match_different_order(self):
    result = self.score(['a', 'b'], ['b', 'a'])
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 1

  def test_should_not_match_with_duplicate_expected_values(self):
    result = self.score(['a', 'a', 'b'], ['a', 'b'])
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 0

  def test_should_not_match_with_duplicate_actual_values(self):
    result = self.score(['a', 'b'], ['a', 'a', 'b'])
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 0

class TestSetScoringType(_TestCommonListScoringType):
  def score(self, *args, **kwargs):
    return SET_SCORING_TYPE.score(*args, **kwargs)

  def test_should_match_different_order(self):
    result = self.score(['a', 'b'], ['b', 'a'])
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 1

  def test_should_match_with_duplicate_expected_values(self):
    result = self.score(['a', 'a', 'b'], ['a', 'b'])
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 1

  def test_should_match_with_duplicate_actual_values(self):
    result = self.score(['a', 'b'], ['a', 'a', 'b'])
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 1
