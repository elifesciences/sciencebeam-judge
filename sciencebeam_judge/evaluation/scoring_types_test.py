from __future__ import division

import logging
from io import BytesIO

import pytest

import numpy as np

from .scoring_types import (
  score_list,
  score_field_as_set,
  resolve_scoring_type,
  ScoringTypes
)

try:
  from cStringIO import StringIO
except ImportError:
  from StringIO import StringIO


LOGGING = logging.getLogger(__name__)

SOME_TEXT = 'test 123'

is_close = lambda a, b: np.allclose([a], [b])

class TestScoreList(object):
  def test_should_score_list_for_exact_match(self):
    result = score_list([SOME_TEXT], [SOME_TEXT])
    assert result['exact']['score'] == 1
    assert result['soft']['score'] == 1
    assert result['levenshtein']['score'] == 1
    assert result['ratcliff_obershelp']['score'] == 1

  def test_should_score_list_for_partial_match_with_spaces(self):
    result = score_list(['a b'], ['ab'])
    assert result['exact']['score'] == 0
    assert result['soft']['score'] == 1
    assert is_close(result['levenshtein']['score'], 2 / 3)
    assert is_close(result['ratcliff_obershelp']['score'], 0.8)

  def test_should_not_convert_to_lower_if_disabled(self):
    result = score_list(['Abc'], ['aBC'], include_values=True, convert_to_lower=False)
    assert result['exact']['expected'] == 'Abc'
    assert result['exact']['actual'] == 'aBC'

  def test_should_convert_to_lower_if_enabled(self):
    result = score_list(['Abc'], ['aBC'], include_values=True, convert_to_lower=True)
    assert result['exact']['expected'] == 'abc'
    assert result['exact']['actual'] == 'abc'

class TestScoreFieldAsSet(object):
  def test_should_match_if_items_match_in_different_order(self):
    result = score_field_as_set(['a', 'b'], ['a', 'b'])
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 1
    assert result['soft']['score'] == 1
    assert result['levenshtein']['score'] == 1
    assert result['ratcliff_obershelp']['score'] == 1

  def test_should_match_empty_lists(self):
    result = score_field_as_set([], [])
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 1

  def test_should_not_match_different_values(self):
    result = score_field_as_set(['a'], ['b'])
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 0

  def test_should_not_match_with_missing_value(self):
    result = score_field_as_set(['a', 'b'], ['a'])
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 0

  def test_should_not_match_with_extra_value(self):
    result = score_field_as_set(['a'], ['a', 'b'])
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 0

  def test_should_normalize_space(self):
    result = score_field_as_set(['a  b'], ['a b'])
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 1

  def test_should_convert_to_lower_if_enabled(self):
    result = score_field_as_set(['a', 'B'], ['A', 'b'], convert_to_lower=True)
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 1

  def test_should_not_convert_to_lower_if_not_enabled(self):
    result = score_field_as_set(['a', 'B'], ['A', 'b'], convert_to_lower=False)
    LOGGING.debug('result: %s', result)
    assert result['exact']['score'] == 0

class TestResolveScoringType(object):
  def test_should_return_string_scoring_type_by_default(self):
    assert resolve_scoring_type(None) == ScoringTypes.STRING

  def test_should_return_string_scoring_type_for_str_as_literal(self):
    assert resolve_scoring_type('str') == ScoringTypes.STRING
    assert resolve_scoring_type('string') == ScoringTypes.STRING

  def test_should_return_string_scoring_type_for_set_as_literal(self):
    assert resolve_scoring_type('set') == ScoringTypes.SET

  def test_should_raise_error_for_invalid_value(self):
    with pytest.raises(ValueError):
      resolve_scoring_type('other')
