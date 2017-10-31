# -*- coding: utf-8 -*-
from __future__ import division

import re
import logging
from difflib import SequenceMatcher

from six import iteritems, raise_from, string_types
from six.moves.configparser import ConfigParser

from lxml import etree as ET
import editdistance

IGNORE_MARKER = '_ignore_'
IGNORE_MARKER_WITH_SPACE = ' ' + IGNORE_MARKER + ' '

flatten = lambda l: [item for sublist in l for item in sublist]

def get_logger():
  return logging.getLogger(__name__)

def force_list(x):
  return x if isinstance(x, list) else [x]

def mean(data):
  return sum(data) / len(data)

def get_full_text(e):
  return "".join(e.itertext())

def get_full_text_ignore_children(e, children_to_ignore):
  if children_to_ignore is None or len(children_to_ignore) == 0:
    return get_full_text(e)
  if e.text is not None:
    return ''.join(e.xpath('text()'))
  return "".join([
    get_full_text_ignore_children(c, children_to_ignore)
    if c not in children_to_ignore else IGNORE_MARKER_WITH_SPACE
    for c in e
  ])

def parse_xml_mapping(xml_mapping_filename_or_fp):
  config = ConfigParser()
  if isinstance(xml_mapping_filename_or_fp, string_types):
    config.read(xml_mapping_filename_or_fp)
  else:
    config.readfp(xml_mapping_filename_or_fp)
  return {
    k: dict(config.items(k))
    for k in config.sections()
  }

def strip_namespace(it):
  for _, el in it:
    if '}' in el.tag:
      el.tag = el.tag.split('}', 1)[1]  # strip all namespaces
  return it

def parse_ignore_namespace(source, filename=None):
  try:
    result = strip_namespace(ET.iterparse(source, recover=True))
    if result.root is None:
      raise RuntimeError('invalid xml {}'.format(filename or source))
    return result.root
  except ET.XMLSyntaxError as e:
    raise_from(RuntimeError('failed to process {}'.format(filename or source)), e)

def parse_xml(source, xml_mapping, fields=None, filename=None):
  root = parse_ignore_namespace(source, filename=filename)
  if not root.tag in xml_mapping:
    raise Exception("unrecognised tag: {} (available: {})".format(root.tag, xml_mapping.sections()))
  mapping = xml_mapping[root.tag]
  field_names = [
    k
    for k in mapping.keys()
    if (fields is None or k in fields) and '.ignore' not in k
  ]
  result = {
    k: [
      get_full_text_ignore_children(
        e,
        e.xpath(mapping[k + '.ignore']) if k + '.ignore' in mapping else None
      ).strip()
      for e in root.xpath(mapping[k])
    ]
    for k in field_names
  }
  return result

FULL_PUNCTUATIONS = u"([ •*,:;?.!/)-−–\"“”‘’'`$]*\u2666\u2665\u2663\u2660\u00A0"
WHITE_SPACE = u" \t\n\r\u00A0"
NBSP = unichr(160)

FULL_PUNCTUATION_AND_WHITESPACE_REGEX = re.compile(
  u'[{}]'.format(re.escape(FULL_PUNCTUATIONS + WHITE_SPACE)))

WHITESPACE_REGEX = re.compile(r'\s+')

def normalize_whitespace(s):
  return WHITESPACE_REGEX.sub(' ', s).replace(NBSP, ' ')

def strip_punctuation_and_whitespace(s):
  return FULL_PUNCTUATION_AND_WHITESPACE_REGEX.sub('', s)

def exact_score(expected, actual):
  return 1 if expected == actual else 0

def levenshtein_score(expected, actual):
  if len(expected) == 0 and len(actual) == 0:
    return 1
  return 1 - (editdistance.eval(expected, actual) / max(len(expected), len(actual)))

def ratcliff_obershelp_score(expected, actual):
  return SequenceMatcher(None, expected, actual).ratio()

def score_obj(expected, actual, value_f, threshold=1, include_values=False):
  binary_expected = 1 if len(expected) > 0 else 0
  # actual will be a false positive (1) if it is populated but expected is not,
  # otherwise it will be positive if it meets the threshold
  value = value_f(expected, actual)
  binary_actual = (
    1
    if len(actual) > 0 and (binary_expected == 0 or (binary_expected == 1 and value >= threshold))
    else 0
  )
  tp = 1 if len(actual) > 0 and len(expected) > 0 and value >= threshold else 0
  tn = 1 if len(actual) == 0 and len(expected) == 0 else 0
  fp = 1 if not tp and len(actual) > 0 else 0
  fn = 1 if not tn and len(actual) == 0 else 0
  d = {
    'expected_something': len(expected) > 0,
    'actual_something': len(actual) > 0,
    'score': value,
    'true_positive': tp,
    'true_negative': tn,
    'false_positive': fp,
    'false_negative': fn,
    'binary_expected': binary_expected,
    'binary_actual': binary_actual
  }
  if include_values:
    d['expected'] = expected
    d['actual'] = actual
  return d

def score_list(expected, actual, include_values=False):
  # sep = '\n'
  sep = ''
  expected_str = normalize_whitespace(sep.join(expected)).lower()
  actual_str = normalize_whitespace(sep.join(actual)).lower()
  return {
    'exact': score_obj(
      expected_str,
      actual_str,
      exact_score,
      include_values=include_values
    ),
    'soft': score_obj(
      strip_punctuation_and_whitespace(expected_str),
      strip_punctuation_and_whitespace(actual_str),
      exact_score,
      include_values=include_values
    ),
    'levenshtein': score_obj(
      expected_str,
      actual_str,
      levenshtein_score,
      0.8,
      include_values=include_values
    ),
    'ratcliff_obershelp': score_obj(
      expected_str,
      actual_str,
      ratcliff_obershelp_score,
      0.95,
      include_values=include_values
    )
  }

def score_results(expected, actual, include_values=False):
  return {
    k: score_list(expected[k], actual[k], include_values=include_values)
    for k in expected.keys()
  }

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
    f: mean([summary_score_map[k][f] for k in keys]) if len(keys) > 0 else 0
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

def comma_separated_str_to_list(s):
  s = s.strip()
  if len(s) == 0:
    return []
  return [item.strip() for item in s.split(',')]
