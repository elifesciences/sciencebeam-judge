from __future__ import division

from io import BytesIO

import numpy as np

from sciencebeam_judge.evaluation_utils import (
  parse_xml,
  normalize_whitespace,
  strip_punctuation_and_whitespace,
  exact_score,
  levenshtein_score,
  ratcliff_obershelp_score,
  score_list,
  score_results,
  comma_separated_str_to_list,
  FULL_PUNCTUATIONS
)

SOME_TEXT = 'test 123'

is_close = lambda a, b: np.allclose([a], [b])

class TestParseXml(object):
  def test_should_parse_single_value_properties(self):
    xml = b'<root><parent><p1>value1</p1><p2>value2</p2></parent></root>'
    xml_mapping = {
      'root': {
        'prop1': 'parent/p1',
        'prop2': 'parent/p2'
      }
    }
    result = parse_xml(BytesIO(xml), xml_mapping)
    assert result == {
      'prop1': ['value1'],
      'prop2': ['value2']
    }

  def test_should_parse_multi_value_properties(self):
    xml = b'<root><parent><p1>value1</p1><p1>value2</p1></parent></root>'
    xml_mapping = {
      'root': {
        'prop1': 'parent/p1'
      }
    }
    result = parse_xml(BytesIO(xml), xml_mapping)
    assert result == {
      'prop1': ['value1', 'value2']
    }

class TestNormalizeWhitespace(object):
  def test_replace_line_feed_with_space(self):
    assert normalize_whitespace('a\nb') == 'a b'

  def test_replace_cr_with_space(self):
    assert normalize_whitespace('a\rb') == 'a b'

  def test_replace_tab_with_space(self):
    assert normalize_whitespace('a\tb') == 'a b'

  def test_replace_npsp_with_space(self):
    assert normalize_whitespace(u'a\u00A0b') == u'a b'

class TestStripPunctuationAndWhitespace(object):
  def test_replace_punctuation_chars(self):
    assert strip_punctuation_and_whitespace(u'a' + FULL_PUNCTUATIONS + 'b') == 'ab'

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

class TestScoreResults(object):
  def test_should_score_results_for_exact_match_and_partial_match(self):
    result = score_results({
      '_exact': [SOME_TEXT],
      '_partial': 'a b'
    }, {
      '_exact': [SOME_TEXT],
      '_partial': 'ab'
    })
    assert result['_exact']['exact']['score'] == 1
    assert result['_exact']['soft']['score'] == 1
    assert result['_partial']['exact']['score'] == 0
    assert result['_partial']['soft']['score'] == 1

class TestCommaSeparatedStrToList(object):
  def test_should_parse_empty_str_as_empty_list(self):
    assert comma_separated_str_to_list('') == []

  def test_should_parse_single_item_str_as_single_item_list(self):
    assert comma_separated_str_to_list('abc') == ['abc']

  def test_should_parse_multiple_item_str(self):
    assert comma_separated_str_to_list('abc,xyz,123') == ['abc', 'xyz', '123']

  def test_should_strip_space_around_items(self):
    assert comma_separated_str_to_list(' abc , xyz , 123 ') == ['abc', 'xyz', '123']
