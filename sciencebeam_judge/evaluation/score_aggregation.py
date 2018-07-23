from __future__ import division

from six import iteritems

from .math import safe_mean


flatten = lambda l: [item for sublist in l for item in sublist]

def force_list(x):
  return x if isinstance(x, list) else [x]

def sum_scores_with_true_negative(scores, total_fields=None):
  tp = sum([s['true_positive'] for s in scores])
  fp = sum([s['false_positive'] for s in scores])
  fn = sum([s['false_negative'] for s in scores])
  d = {
    'true_positive': tp,
    'false_positive': fp,
    'false_negative': fn
  }
  if total_fields is not None:
    tn = total_fields - tp - fp - fn
    d['true_negative'] = tn
  return d

def precision_for_tp_fp(tp, fp, na=0):
  return tp / (tp + fp) if tp + fp > 0 else na

def recall_for_tp_fn_fp(tp, fn, fp, na=0):
  return tp / (tp + fn + fp) if tp + fn > 0 else na

def f1_for_precision_recall(precision, recall, na=0):
  return 2 * (precision * recall) / (precision + recall) if precision + recall > 0 else na

def summary_score(sum_scores):
  tp = sum_scores['true_positive']
  fp = sum_scores['false_positive']
  fn = sum_scores['false_negative']
  tn = sum_scores['true_negative']
  accuracy = (tp + tn) / (tp + fp + tn + fn) if tp + fp + tn + fn > 0 else 0
  precision = precision_for_tp_fp(tp, fp)
  recall = recall_for_tp_fn_fp(tp, fn, fp)
  f1 = f1_for_precision_recall(precision, recall)
  return {
    'accuracy': accuracy,
    'precision': precision,
    'recall': recall,
    'f1': f1
  }

def scoring_method_as_top_level_key(scores):
  d = dict()
  for k_field, scoring_methods in iteritems(scores):
    for k_scoring_method, results in iteritems(scoring_methods):
      d.setdefault(k_scoring_method, {})[k_field] = results
  return d

def compact_scores(scores, total_fields=None, keys=None):
  if not scores:
    return {}
  if keys is None:
    keys = scores.keys()
  return {
    k: sum_scores_with_true_negative(scores[k], total_fields)
    for k in keys
  }

def combine_scores(list_of_scores, keys=None):
  if not list_of_scores:
    return {}
  combined_scores = dict()
  for scores in list_of_scores:
    for k, v in iteritems(scores):
      if keys is None or k in keys:
        combined_scores.setdefault(k, []).extend(
          v if isinstance(v, list) else [v]
        )
  return combined_scores

def combine_and_compact_scores_by_scoring_method(list_of_scores):
  if not list_of_scores:
    return {}
  combined_scores = dict()
  for scores in list_of_scores:
    for k_scoring_method, scores_by_field in iteritems(scores):
      combined_scores.setdefault(k_scoring_method, []).append(
        scores_by_field
      )
  return {
    k_scoring_method: compact_scores(combine_scores(list_of_scores_by_field))
    for k_scoring_method, list_of_scores_by_field in iteritems(combined_scores)
  }

def combine_and_compact_scores_by_scoring_method_with_count(list_of_scores_with_count):
  return (
    combine_and_compact_scores_by_scoring_method(
      list_of_scores for list_of_scores, _ in list_of_scores_with_count
    ),
    sum(
      count for _, count in list_of_scores_with_count
    )
  )

def summarise_binary_results(scores, keys, count=None):
  # get_logger().info('summarise_binary_results, scores: %s', scores)
  scores = {k: force_list(x) for k, x in iteritems(scores)}
  score_fields = ['accuracy', 'precision', 'recall', 'f1']
  # if not isinstance(scores, list):
  #   scores = [scores]
  total_fields = sum([
    s['true_positive'] + s['false_negative'] + 2 * s['false_positive']
    for s in flatten([scores[k] for k in keys])
  ])
  sum_scores_map = {k: sum_scores_with_true_negative(scores[k], total_fields) for k in keys}
  summary_score_map = {k: summary_score(sum_scores_map[k]) for k in keys}
  total_sums = {
    k: sum(sum_scores[k] for sum_scores in sum_scores_map.values())
    for k in ['true_positive', 'false_negative', 'false_positive', 'true_negative']
  }
  micro_avg_scores = summary_score(total_sums)
  macro_avg_scores = {
    f: safe_mean([summary_score_map[k][f] for k in keys])
    for f in score_fields
  }
  return {
    'by-field': {
      k: {
        'total': sum_scores_map[k],
        'scores': summary_score_map.get(k)
      }
      for k in keys
    },
    'total': total_sums,
    'micro': micro_avg_scores,
    'macro': macro_avg_scores,
    'count': count
  }

def summarise_results_by_scoring_method(scores, keys, count=None):
  # get_logger().info('!!!!! scores: %s', scores)
  return {
    k_scoring_method: summarise_binary_results(
      scores_by_field,
      keys=keys,
      count=count
    )
    for k_scoring_method, scores_by_field in iteritems(scores)
  }

def summarise_results_by_scoring_method_with_count(scores_with_count, keys):
  return summarise_results_by_scoring_method(
    scores_with_count[0],
    keys,
    count=scores_with_count[1]
  )
