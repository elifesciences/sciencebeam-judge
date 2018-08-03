from .items import (
  _get_exact_matched_characters,
  _get_fuzzy_matched_characters
)


UNICODE_CHAR = u'\u2013'
UNICODE_STR = u'Unicode %s' % UNICODE_CHAR


class TestGetExactMatchedCharacters(object):
  def test_should_match_all_characters(self):
    assert _get_exact_matched_characters('abc', ['ab', 'c']) == [True] * 3

  def test_should_match_some_characters(self):
    assert _get_exact_matched_characters('abc', ['ab', 'd']) == [True, True, False]

class TestGetFuzzyMatchedCharacters(object):
  def test_should_match_all_characters(self):
    assert _get_fuzzy_matched_characters('abc', ['ab', 'c'], threshold=1) == [True] * 3

  def test_should_match_some_characters(self):
    assert _get_fuzzy_matched_characters('abc', ['ab', 'd'], threshold=1) == [True, True, False]

  def test_should_fuzzy_match_characters_above_threshold(self):
    assert _get_fuzzy_matched_characters('abc', ['abd'], threshold=0.5) == [True, True, False]

  def test_should_not_fuzzy_match_characters_below_threshold(self):
    assert _get_fuzzy_matched_characters('abc', ['abd'], threshold=0.9) == [False] * 3

  def test_should_fuzzy_match_unicode_characters(self):
    assert _get_fuzzy_matched_characters(
      UNICODE_STR, [UNICODE_STR], threshold=0.9
    ) == [True] * len(UNICODE_STR)
