from __future__ import division

import logging

from .scoring_methods import (
  exact_score,
  levenshtein_score,
  ratcliff_obershelp_score
)

from .math import is_close


LOGGING = logging.getLogger(__name__)

SOME_TEXT = 'test 123'

class TestExactScore(object):
  def test_should_return_one_for_exact_match(self):
    assert exact_score(SOME_TEXT, SOME_TEXT) == 1

  def test_should_return_zero_for_any_mismatch(self):
    assert exact_score(SOME_TEXT, SOME_TEXT[:-1] + 'X') == 0

class TestLevenshteinScore(object):
  def test_should_return_one_for_exact_match(self):
    assert levenshtein_score(SOME_TEXT, SOME_TEXT) == 1

  def test_should_return_two_third_for_a_two_third_match(self):
    assert is_close(levenshtein_score('axb', 'ayb'), 2 / 3)

  def test_should_return_zero_for_no_match(self):
    assert levenshtein_score('abc', 'xyz') == 0

class TestRatcliffObershelpScore(object):
  def test_should_return_one_for_exact_match(self):
    assert ratcliff_obershelp_score(SOME_TEXT, SOME_TEXT) == 1

  def test_should_return_0666_for_a_two_third_match(self):
    assert is_close(ratcliff_obershelp_score('axb', 'ayb'), 2 / 3)

  def test_should_return_zero_for_no_match(self):
    assert ratcliff_obershelp_score('abc', 'xyz') == 0
