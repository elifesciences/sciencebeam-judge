from __future__ import division

import logging

import numpy as np

from .scoring_types import score_field_as_string


LOGGING = logging.getLogger(__name__)

SOME_TEXT = 'test 123'

is_close = lambda a, b: np.allclose([a], [b])

class TestScoreList(object):
  def test_should_score_list_for_exact_match(self):
    result = score_field_as_string([SOME_TEXT], [SOME_TEXT])
    assert result['exact']['score'] == 1
    assert result['soft']['score'] == 1
    assert result['levenshtein']['score'] == 1
    assert result['ratcliff_obershelp']['score'] == 1

  def test_should_score_list_for_partial_match_with_spaces(self):
    result = score_field_as_string(['a b'], ['ab'])
    assert result['exact']['score'] == 0
    assert result['soft']['score'] == 1
    assert is_close(result['levenshtein']['score'], 2 / 3)
    assert is_close(result['ratcliff_obershelp']['score'], 0.8)

  def test_should_not_convert_to_lower_if_disabled(self):
    result = score_field_as_string(['Abc'], ['aBC'], include_values=True, convert_to_lower=False)
    assert result['exact']['expected'] == 'Abc'
    assert result['exact']['actual'] == 'aBC'

  def test_should_convert_to_lower_if_enabled(self):
    result = score_field_as_string(['Abc'], ['aBC'], include_values=True, convert_to_lower=True)
    assert result['exact']['expected'] == 'abc'
    assert result['exact']['actual'] == 'abc'
