import numpy as np

from .score_aggregation import (
  scoring_method_as_top_level_key,
  compact_scores,
  combine_scores,
  combine_and_compact_scores_by_scoring_method,
  summarise_binary_results,
  precision_for_tp_fp,
  recall_for_tp_fn_fp,
  f1_for_precision_recall
)

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