from __future__ import division

from io import BytesIO

import numpy as np

from sciencebeam_judge.evaluation_utils import (
  parse_xml_mapping,
  parse_xml,
  normalize_whitespace,
  strip_punctuation_and_whitespace,
  exact_score,
  levenshtein_score,
  ratcliff_obershelp_score,
  score_list,
  score_results,
  summarise_binary_results,
  precision_for_tp_fp,
  recall_for_tp_fn_fp,
  f1_for_precision_recall,
  comma_separated_str_to_list,
  FULL_PUNCTUATIONS
)

try:
  from cStringIO import StringIO
except ImportError:
  from StringIO import StringIO

SOME_TEXT = 'test 123'

is_close = lambda a, b: np.allclose([a], [b])

class TestParseXmlMapping(object):
  def test_should_parse_multiple_sections(self):
    xml_mapping = u'''
[root1]
prop1 = parent1/p1
prop2 = parent1/p2

[root2]
prop1 = parent2/p1
prop2 = parent2/p2
'''.strip()
    expected_xml_mapping = {
      'root1': {
        'prop1': 'parent1/p1',
        'prop2': 'parent1/p2'
      },
      'root2': {
        'prop1': 'parent2/p1',
        'prop2': 'parent2/p2'
      }
    }
    result = parse_xml_mapping(StringIO(xml_mapping))
    assert result == expected_xml_mapping

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

class TestSummariseBinaryResults(object):
  def test_should_return_zero_results_for_no_values(self):
    scores = {
      'key1': [
      ]
    }
    result = summarise_binary_results(scores, keys=['key1'])
    key1_results = result.get('by-field', {}).get('key1', {})
    key1_totals = key1_results.get('total', {})
    assert key1_totals.get('true_positive') == 0
    assert key1_totals.get('false_positive') == 0
    assert key1_totals.get('false_negative') == 0
    assert key1_totals.get('true_negative') == 0

  def test_should_return_sum_individual_counts_and_calculate_f1(self):
    scores = {
      'key1': [{
        'true_positive': 1,
        'false_positive': 0,
        'false_negative': 0
      }, {
        'true_positive': 0,
        'false_positive': 1,
        'false_negative': 0
      }]
    }
    result = summarise_binary_results(scores, keys=['key1'])
    key1_results = result.get('by-field', {}).get('key1', {})
    key1_totals = key1_results.get('total', {})
    key1_scores = key1_results.get('scores', {})
    assert key1_totals.get('true_positive') == 1
    assert key1_totals.get('false_positive') == 1
    assert key1_totals.get('false_negative') == 0
    assert key1_scores.get('f1') == 0.5
    assert key1_scores.get('precision') == 0.5
    assert key1_scores.get('recall') == 0.5
    # since there is no other field
    assert result.get('total') == key1_totals
    assert result.get('micro') == key1_scores
    assert result.get('macro') == key1_scores

  def test_should_return_calculate_f1_for_multiple_keys(self):
    scores = {
      'key1': [{
        'true_positive': 1,
        'false_positive': 1,
        'false_negative': 0
      }],
      'key2': [{
        'true_positive': 1,
        'false_positive': 0,
        'false_negative': 1
      }]
    }
    result = summarise_binary_results(scores, keys=['key1', 'key2'])
    key1_results = result.get('by-field', {}).get('key1', {})
    key1_totals = key1_results.get('total', {})
    key1_scores = key1_results.get('scores', {})
    micro_avg = result.get('micro', {})
    macro_avg = result.get('macro', {})
    assert key1_totals.get('true_positive') == 1
    assert key1_totals.get('false_positive') == 1
    assert key1_totals.get('false_negative') == 0
    assert key1_scores.get('precision') == 0.5
    assert key1_scores.get('recall') == 0.5
    assert key1_scores.get('f1') == 0.5

    key2_results = result.get('by-field', {}).get('key2', {})
    key2_totals = key2_results.get('total', {})
    key2_scores = key2_results.get('scores', {})
    assert key2_totals.get('true_positive') == 1
    assert key2_totals.get('false_positive') == 0
    assert key2_totals.get('false_negative') == 1
    assert key2_scores.get('precision') == 1.0
    assert key2_scores.get('recall') == 0.5
    assert key2_scores.get('f1') == f1_for_precision_recall(
      key2_scores.get('precision'),
      key2_scores.get('recall')
    )

    assert macro_avg.get('precision') == np.mean([
      key1_scores.get('precision'),
      key2_scores.get('precision')
    ])
    assert macro_avg.get('recall') == np.mean([
      key1_scores.get('recall'),
      key2_scores.get('recall')
    ])
    assert macro_avg.get('f1') == np.mean([
      key1_scores.get('f1'),
      key2_scores.get('f1')
    ])

    assert micro_avg.get('precision') == precision_for_tp_fp(
      key1_totals.get('true_positive') + key2_totals.get('true_positive'),
      key1_totals.get('false_positive') + key2_totals.get('false_positive')
    )
    assert micro_avg.get('recall') == recall_for_tp_fn_fp(
      key1_totals.get('true_positive') + key2_totals.get('true_positive'),
      key1_totals.get('false_negative') + key2_totals.get('false_negative'),
      key1_totals.get('false_positive') + key2_totals.get('false_positive')
    )
    assert micro_avg.get('f1') == f1_for_precision_recall(
      micro_avg.get('precision'),
      micro_avg.get('recall')
    )

class TestCommaSeparatedStrToList(object):
  def test_should_parse_empty_str_as_empty_list(self):
    assert comma_separated_str_to_list('') == []

  def test_should_parse_single_item_str_as_single_item_list(self):
    assert comma_separated_str_to_list('abc') == ['abc']

  def test_should_parse_multiple_item_str(self):
    assert comma_separated_str_to_list('abc,xyz,123') == ['abc', 'xyz', '123']

  def test_should_strip_space_around_items(self):
    assert comma_separated_str_to_list(' abc , xyz , 123 ') == ['abc', 'xyz', '123']
