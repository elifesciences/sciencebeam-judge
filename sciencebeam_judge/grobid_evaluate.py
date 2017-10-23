from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import argparse
import os
import json
from multiprocessing import Pool
from functools import partial
from contextlib import contextmanager
import logging

from tqdm import tqdm

from sciencebeam_judge.evaluation_utils import (
  parse_xml,
  parse_xml_mapping,
  score_results,
  comma_separated_str_to_list
)

flatten = lambda l: [item for sublist in l for item in sublist]

def get_logger():
  return logging.getLogger(__name__)

def mean(data):
  return sum(data) / len(data)

def get_filename_basename(filename):
  return os.path.splitext(filename)[0]

def get_filename_ext(filename):
  return os.path.splitext(os.path.basename(filename))[1]

def collect_results_for_directory(
  sub_directory_path,
  xml_mapping_filename,
  target_suffix,
  prediction_suffix,
  field_names):
  get_logger().debug("sub_directory_path: %s", sub_directory_path)

  filenames = [
    s for s in os.listdir(sub_directory_path)
    if os.path.isfile(os.path.join(sub_directory_path, s))
  ]
  target_filenames = [
    s for s in filenames
    if s.endswith(target_suffix)
  ]
  prediction_filenames = [
    s for s in filenames
    if s.endswith(prediction_suffix)
  ]
  if len(target_filenames) == 0:
    raise Exception(
      "no target file found in {}".format(sub_directory_path)
    )
  if len(prediction_filenames) == 0:
    raise Exception(
      "no prediction file found in {}".format(sub_directory_path)
    )
  if len(target_filenames) > 1:
    raise Exception(
      "too many target files found in {} ({})".format(sub_directory_path, target_filenames)
      )
  if len(prediction_filenames) > 1:
    raise Exception(
      "too many prediction files found in {} ({})".format(sub_directory_path, prediction_filenames)
    )
  full_target_xml_filename = os.path.join(sub_directory_path, target_filenames[0])
  full_prediction_xml_filename = os.path.join(sub_directory_path, prediction_filenames[0])
  xml_mapping = parse_xml_mapping(xml_mapping_filename)
  target_xml = parse_xml(full_target_xml_filename, xml_mapping, fields=field_names)
  prediction_xml = parse_xml(full_prediction_xml_filename, xml_mapping, fields=field_names)
  return score_results(target_xml, prediction_xml)

def collect_results_for_directory_log_exception(sub_directory_path, **kwargs):
  try:
    return collect_results_for_directory(sub_directory_path, **kwargs)
  except Exception as e:
    get_logger().exception('failed to process directory', exc_info=e)
    return None

def summary_score(sum_scores):
  tp = sum_scores['true_positive']
  fp = sum_scores['false_positive']
  fn = sum_scores['false_negative']
  tn = sum_scores['true_negative']
  accuracy = (tp + tn) / (tp + fp + tn + fn) if tp + fp + tn + fn > 0 else 0
  precision = tp / (tp + fp) if tp + fp > 0 else 0
  recall = tp / (tp + fn + fp) if tp + fn > 0 else 0
  f1 = 2 * (precision * recall) / (precision + recall) if precision + recall > 0 else 0
  return {
    'accuracy': accuracy,
    'precision': precision,
    'recall': recall,
    'f1': f1
  }

def sum_scores_with_true_negative(scores, total_fields):
  tp = sum([s['true_positive'] for s in scores])
  fp = sum([s['false_positive'] for s in scores])
  fn = sum([s['false_negative'] for s in scores])
  tn = total_fields - tp - fp - fn
  return {
    'true_positive': tp,
    'false_positive': fp,
    'false_negative': fn,
    'true_negative': tn
  }

def summarise_binary_results(scores, keys):
  score_fields = ['accuracy', 'precision', 'recall', 'f1']
  total_fields = sum([
    s['true_positive'] + s['false_negative'] + 2 * s['false_positive']
    for s in flatten([scores[k] for k in keys])
  ])
  sum_scores_map = {k: sum_scores_with_true_negative(scores[k], total_fields) for k in keys}
  summary_score_map = {k: summary_score(sum_scores_map[k]) for k in keys}
  summary_scores = [(k, summary_score_map[k]) for k in keys]
  micro_avg_scores = summary_score({
    k: sum(sum_scores[k] for sum_scores in sum_scores_map.values())
    for k in ['true_positive', 'false_negative', 'false_positive', 'true_negative']
  })
  macro_avg_scores = {
    f: mean([summary_score_map[k][f] for k in keys]) if len(keys) > 0 else 0
    for f in score_fields
  }
  rows = [
    ['label'] + score_fields,
    []
  ] + [
    [k] + [score[f] * 100 for f in score_fields]
    for k, score in summary_scores
  ] + [
    []
  ] + [
    ['all fields'] +
    [micro_avg_scores[f] * 100 for f in score_fields] +
    ['(micro average)']
  ] + [
    [] +
    [macro_avg_scores[f] * 100 for f in score_fields] +
    ['(macro average)']
  ]
  rows = [['{:.2f}'.format(x) if not isinstance(x, str) else x for x in row] for row in rows]
  column_widths = [20, 10, 10, 10, 10, 20]
  rows = [[x.rjust(c, ' ') for x, c in zip(row, column_widths)] for row in rows]
  return '\n'.join([' '.join(row) for row in rows])

def summarise_results(results, keys):
  available_keys = set(flatten([r.keys() for r in results]))
  keys = [k for k in keys if k in available_keys]
  return\
  """
  ======= Strict Matching ======= (exact matches)

  ===== Field-level results =====

  {exact_results}

  ======== Soft Matching ======== (ignoring punctuation, case and space characters mismatches)

  ===== Field-level results =====

  {soft_results}

  ==== Levenshtein Matching ===== (Minimum Levenshtein distance at 0.8)

  ===== Field-level results =====

  {levenshtein_results}

  = Ratcliff/Obershelp Matching = (Minimum Ratcliff/Obershelp similarity at 0.95)

  ===== Field-level results =====

  {ratcliff_obershelp_results}


  """.format(
    exact_results=summarise_binary_results({
      k: [r[k]['exact'] for r in results]
      for k in keys
    }, keys),
    soft_results=summarise_binary_results({
      k: [r[k]['soft'] for r in results]
      for k in keys
    }, keys),
    levenshtein_results=summarise_binary_results({
      k: [r[k]['levenshtein'] for r in results]
      for k in keys
    }, keys),
    ratcliff_obershelp_results=summarise_binary_results({
      k: [r[k]['ratcliff_obershelp'] for r in results]
      for k in keys
    }, keys)
  )

@contextmanager
def terminating(thing):
  try:
    yield thing
  finally:
    thing.terminate()

def create_pool(**kwargs):
  return terminating(Pool(**kwargs))

def tqdm_multiprocessing_map(f, iterable, processes=None):
  with create_pool(processes=processes) as p:
    with tqdm(total=len(iterable)) as pbar:
      result = []
      imap_result = p.imap(f, iterable)
      for x in imap_result:
        pbar.update()
        result.append(x)
      return result

def evaluate_results(data_path, field_names, sequential, **other_options):
  get_logger().info("data path: %s", data_path)
  sub_directory_names = sorted([
    os.path.join(data_path, s)
    for s in os.listdir(data_path)
    if os.path.isdir(os.path.join(data_path, s))
  ])
  get_logger().info("sub directories: %s", len(sub_directory_names))
  if sequential:
    process_sub_directory = partial(
      collect_results_for_directory,
      field_names=field_names,
      **other_options
    )
    results = [
      process_sub_directory(sub_directory)
      for sub_directory in sub_directory_names
    ]
  else:
    process_sub_directory = partial(
      collect_results_for_directory_log_exception,
      field_names=field_names,
      **other_options
    )
    results = tqdm_multiprocessing_map(
      process_sub_directory,
      sub_directory_names
    )
  debug_enabled = False
  if debug_enabled:
    get_logger().debug('results:\n%s', json.dumps(results, sort_keys=True, indent=2))
  print(summarise_results(
    [r for r in results if r is not None],
    keys=field_names
  ))

def parse_args():
  parser = argparse.ArgumentParser(
    description=(
      "Evaluate results, closely matching GROBID's end-to-end evaluation"
      "\n(JATS XML and TEI XML are supported via xml-mapping.conf)"
    )
  )
  parser.add_argument(
    '--data-path',
    type=str,
    required=True,
    help='path to data directory containing sub directories with target and predicted XML'
  )
  parser.add_argument(
    '--xml-mapping',
    type=str,
    default='xml-mapping.conf',
    help='filename to the xml mapping configuration'
  )
  parser.add_argument(
    '--target-suffix',
    type=str,
    default='.nxml',
    help='filename suffix for target XML files'
  )
  parser.add_argument(
    '--prediction-suffix',
    type=str,
    default='.tei.xml',
    help='filename suffix for prediction XML files'
  )
  parser.add_argument(
    '--fields',
    type=comma_separated_str_to_list,
    default=['abstract', 'authors', 'first_author', 'keywords', 'title'],
    help='comma separated list of fields to process'
  )
  parser.add_argument(
    '--sequential',
    action='store_true',
    help='Disables parallel processing. Useful for debugging.'
  )
  args = parser.parse_args()
  return args

def main():
  options = parse_args()

  # validate xml mapping
  parse_xml_mapping(options.xml_mapping)

  evaluate_results(
    data_path=options.data_path,
    xml_mapping_filename=options.xml_mapping,
    target_suffix=options.target_suffix,
    prediction_suffix=options.prediction_suffix,
    field_names=options.fields,
    sequential=options.sequential
  )
  get_logger().info("done")

if __name__ == "__main__":
  logging.basicConfig()

  main()
