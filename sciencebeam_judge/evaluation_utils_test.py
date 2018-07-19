from __future__ import division

import logging
from io import BytesIO

import numpy as np

from sciencebeam_judge.evaluation_utils import (
  parse_xml_mapping,
  parse_xml,
  scoring_method_as_top_level_key,
  score_results,
  compact_scores,
  combine_scores,
  combine_and_compact_scores_by_scoring_method,
  summarise_binary_results,
  precision_for_tp_fp,
  recall_for_tp_fn_fp,
  f1_for_precision_recall,
  comma_separated_str_to_list
)

try:
  from cStringIO import StringIO
except ImportError:
  from StringIO import StringIO


LOGGING = logging.getLogger(__name__)

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

class TestScoringMethodAsTopLevelKey(object):
  def test_should_move_scoring_method_up(self):
    assert scoring_method_as_top_level_key({
      'key1': {
        'exact': {
          'true_positive': 0,
          'false_positive': 1,
          'false_negative': 0
        }, 'soft': {
          'true_positive': 1,
          'false_positive': 0,
          'false_negative': 0
        }
      }
    }) == {
      'exact': {
        'key1': {
          'true_positive': 0,
          'false_positive': 1,
          'false_negative': 0
        }
      },
      'soft': {
        'key1': {
          'true_positive': 1,
          'false_positive': 0,
          'false_negative': 0
        }
      }
    }

class TestCompactScores(object):
  def test_should_total_scores_by_key(self):
    scores = {
      'key1': [{
        'true_positive': 1,
        'false_positive': 0,
        'false_negative': 0
      }, {
        'true_positive': 0,
        'false_positive': 1,
        'false_negative': 0
      }],
      'key2': [{
        'true_positive': 1,
        'false_positive': 0,
        'false_negative': 1
      }]
    }
    result = compact_scores(scores)
    assert result == {
      'key1': {
        'true_positive': 1,
        'false_positive': 1,
        'false_negative': 0
      },
      'key2': {
        'true_positive': 1,
        'false_positive': 0,
        'false_negative': 1
      }
    }

class TestCombineScores(object):
  def test_should_combine_scores_by_key(self):
    list_of_scores = [{
      'key1': {
        'true_positive': 1,
        'false_positive': 0,
        'false_negative': 0
      }
    }, {
      'key1': {
        'true_positive': 0,
        'false_positive': 1,
        'false_negative': 0
      },
    }, {
      'key2': {
        'true_positive': 1,
        'false_positive': 0,
        'false_negative': 1
      }
    }]
    combined_scores = {
      'key1': [{
        'true_positive': 1,
        'false_positive': 0,
        'false_negative': 0
      }, {
        'true_positive': 0,
        'false_positive': 1,
        'false_negative': 0
      }],
      'key2': [{
        'true_positive': 1,
        'false_positive': 0,
        'false_negative': 1
      }]
    }
    result = combine_scores(list_of_scores)
    assert result == combined_scores

class TestCombineAndCompactScoresByScoringMethod(object):
  def test_x(self):
    list_of_scores = [{
      'exact': {
        'key1': {
          'true_positive': 1,
          'false_positive': 0,
          'false_negative': 0
        }
      }
    }, {
      'exact': {
        'key1': {
          'true_positive': 0,
          'false_positive': 1,
          'false_negative': 0
        }
      },
      'soft': {
        'key1': {
          'true_positive': 1,
          'false_positive': 0,
          'false_negative': 0
        },
        'key2': {
          'true_positive': 0,
          'false_positive': 0,
          'false_negative': 1
        }
      }
    }]
    combined_scores = {
      'exact': {
        'key1': {
          'true_positive': 1,
          'false_positive': 1,
          'false_negative': 0
        }
      },
      'soft': {
        'key1': {
          'true_positive': 1,
          'false_positive': 0,
          'false_negative': 0
        },
        'key2': {
          'true_positive': 0,
          'false_positive': 0,
          'false_negative': 1
        }
      }
    }
    assert combine_and_compact_scores_by_scoring_method(list_of_scores) == combined_scores

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
