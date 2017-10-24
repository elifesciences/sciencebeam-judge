from __future__ import absolute_import

import argparse
import os
import subprocess
import errno
import logging
from itertools import groupby
from io import BytesIO
from functools import partial
import csv

import apache_beam as beam
from apache_beam.io.filesystems import FileSystems
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions

from six import iteritems, string_types

from sciencebeam_judge.beam_utils.workaround_textio import (
  WriteToText
)

from sciencebeam_judge.evaluation_utils import (
  parse_xml,
  parse_xml_mapping,
  score_results,
  scoring_method_as_top_level_key,
  combine_and_compact_scores_by_scoring_method,
  combine_scores,
  compact_scores,
  summarise_binary_results,
  summarise_results_by_scoring_method,
  comma_separated_str_to_list
)

try:
  from cStringIO import StringIO
except ImportError:
  from StringIO import StringIO


def get_logger():
  return logging.getLogger(__name__)

def create_fn_api_runner():
  from apache_beam.runners.portability.fn_api_runner import FnApiRunner
  return FnApiRunner()

def Spy(f):
  def spy_wrapper(x):
    f(x)
    return x
  return spy_wrapper

def MapSpy(f):
  return beam.Map(Spy(f))

def find_matching_filenames(pattern):
  return [x.path for x in FileSystems.match([pattern])[0].metadata_list]

def group_files_by_parent_directory(filenames):
  return {
    k: list(v)
    for k, v in groupby(sorted(filenames), lambda x: os.path.dirname(x))
  }

def zip_by_keys(d1, d2):
  return (
    (d1.get(k), d2.get(k))
    for k in sorted(set(d1.keys()) | set(d2.keys()))
  )

def FindFilePairs(x):
  data_path = x['data_path']
  prediction_suffix = x['prediction_suffix']
  target_suffix = x['target_suffix']
  prediction_pattern = os.path.join(data_path, '*/*' + prediction_suffix)
  target_pattern = os.path.join(data_path, '*/*' + target_suffix)
  all_prediction_files = find_matching_filenames(prediction_pattern)
  all_target_files = find_matching_filenames(target_pattern)
  get_logger().info(
    'found files: prediction: %d, target: %d',
    len(all_prediction_files), len(all_target_files)
  )
  grouped_prediction_files = group_files_by_parent_directory(all_prediction_files)
  grouped_target_files = group_files_by_parent_directory(all_target_files)
  for prediction_files, target_files in zip_by_keys(
    grouped_prediction_files, grouped_target_files):

    if len(prediction_files or []) == 1 and len(target_files or []) == 1:
      yield {
        'prediction_file': prediction_files[0],
        'target_file': target_files[0]
      }
    else:
      get_logger().info(
        'no exclusively matching files found: prediction: %s, target: %s',
        prediction_files, target_files
      )

def read_all_from_path(path):
  buffer_size = 4096 * 1024
  with FileSystems.open(path) as f:
    out = BytesIO()
    while True:
      buf = f.read(buffer_size)
      if not buf:
        break
      out.write(buf)
    return out.getvalue()

def ReadFilePairs(x):
  prediction_file = x['prediction_file']
  target_file = x['target_file']
  prediction_content = read_all_from_path(prediction_file)
  target_content = read_all_from_path(target_file)
  d = dict(x)
  d['prediction_content'] = prediction_content
  d['target_content'] = target_content
  return d

def EvaluateFilePairs(x, xml_mapping, field_names):
  prediction_content = x['prediction_content']
  target_content = x['target_content']
  prediction_xml = parse_xml(BytesIO(prediction_content), xml_mapping, fields=field_names)
  target_xml = parse_xml(BytesIO(target_content), xml_mapping, fields=field_names)
  d = dict(x)
  d['evaluation_results'] = score_results(target_xml, prediction_xml, include_values=True)
  return d

class OutputColumns(object):
  PREDICTION_FILE = 'prediction_file'
  TARGET_FILE = 'target_file'
  FIELD_NAME = 'field_name'
  EVALUATION_METHOD = 'evaluation_method'
  TP = 'tp'
  FP = 'fp'
  FN = 'fn'
  TN = 'tn'
  EXPECTED = 'expected'
  ACTUAL = 'actual'

DEFAULT_OUTPUT_COLUMNS = [
  OutputColumns.PREDICTION_FILE,
  OutputColumns.TARGET_FILE,
  OutputColumns.FIELD_NAME,
  OutputColumns.EVALUATION_METHOD,
  OutputColumns.TP,
  OutputColumns.FP,
  OutputColumns.FN,
  OutputColumns.TN,
  OutputColumns.EXPECTED,
  OutputColumns.ACTUAL
]

class SummaryOutputColumns(object):
  EVALUATION_METHOD = 'evaluation_method'
  FIELD_NAME = 'field_name'
  STATS_NAME = 'stats_name'
  TP = 'tp'
  FP = 'fp'
  FN = 'fn'
  TN = 'tn'
  PRECISION = 'precision'
  RECALL = 'recall'
  F1 = 'f1'

DEFAULT_SUMMARY_OUTPUT_COLUMNS = [
  SummaryOutputColumns.EVALUATION_METHOD,
  SummaryOutputColumns.FIELD_NAME,
  SummaryOutputColumns.STATS_NAME,
  SummaryOutputColumns.TP,
  SummaryOutputColumns.FP,
  SummaryOutputColumns.FN,
  SummaryOutputColumns.TN,
  SummaryOutputColumns.PRECISION,
  SummaryOutputColumns.RECALL,
  SummaryOutputColumns.F1
]

def FlattenEvaluationResults(field_names):
  def wrapper(x):
    C = OutputColumns
    prediction_file = x['prediction_file']
    target_file = x['target_file']
    results = x['evaluation_results']
    flat_result = []
    for field_name in field_names:
      for evaluation_method, evaluation_result in iteritems(results[field_name]):
        flat_result.append({
          C.PREDICTION_FILE: os.path.basename(prediction_file),
          C.TARGET_FILE: os.path.basename(target_file),
          C.FIELD_NAME: field_name,
          C.EVALUATION_METHOD: evaluation_method,
          C.TP: evaluation_result['true_positive'],
          C.FP: evaluation_result['false_positive'],
          C.FN: evaluation_result['false_negative'],
          C.TN: evaluation_result['true_negative'],
          C.EXPECTED: evaluation_result['expected'],
          C.ACTUAL: evaluation_result['actual']
        })
    return flat_result
  return wrapper

def flatten_summary_results(summary_by_scoring_method):
  C = SummaryOutputColumns
  flat_result = []
  for scoring_method, summary in iteritems(summary_by_scoring_method):
    for field_name, field_summary in iteritems(summary['by-field']):
      field_totals = field_summary['total']
      field_scores = field_summary['scores']
      flat_result.append({
        C.EVALUATION_METHOD: scoring_method,
        C.FIELD_NAME: field_name,
        C.TP: field_totals['true_positive'],
        C.FP: field_totals['false_positive'],
        C.FN: field_totals['false_negative'],
        C.TN: field_totals['true_negative'],
        C.PRECISION: field_scores['precision'],
        C.RECALL: field_scores['recall'],
        C.F1: field_scores['f1']
      })
    for stats_name in ['micro', 'macro']:
      stats = summary[stats_name]
      flat_result.append({
        C.EVALUATION_METHOD: scoring_method,
        C.STATS_NAME: stats_name,
        C.PRECISION: stats['precision'],
        C.RECALL: stats['recall'],
        C.F1: stats['f1']
      })
  return flat_result

def format_csv_rows(rows):
  get_logger().info('format_csv_rows, rows: %s', rows)
  out = BytesIO()
  writer = csv.writer(out)
  writer.writerows([
    [
      x.encode('utf-8') if isinstance(x, string_types) else x
      for x in row
    ]
    for row in rows
  ])
  result = out.getvalue().decode('utf-8').rstrip('\r\n')
  get_logger().info('format_csv_rows, result: %s', result)
  return result

def FormatCsv(x):
  return format_csv_rows([x])

def DictToList(fields):
  def wrapper(x):
    get_logger().info('DictToList: %s -> %s', fields, x)
    return [x.get(field) for field in fields]
  return wrapper

class WriteDictCsv(beam.PTransform):
  def __init__(self, path, columns, file_name_suffix=None):
    super(WriteDictCsv, self).__init__()
    self.path = path
    self.columns = columns
    self.file_name_suffix = file_name_suffix

  def expand(self, pcoll):
    return (
      pcoll |
      "ToList" >> beam.Map(DictToList(self.columns)) |
      "Format" >> beam.Map(FormatCsv) |
      "LogFormattedCsv" >> MapSpy(
        lambda x: get_logger().info('formatted csv: %s', x)
      ) |
      "Write" >> WriteToText(
        self.path,
        file_name_suffix=self.file_name_suffix,
        header=format_csv_rows([self.columns])
      )
    )

def combine_evaluation_results(evaluation_results):
  get_logger().info('!!!!!!!!!! evaluation_results: %s (%d)', str(evaluation_results)[:50], len(evaluation_results))
  return combine_and_compact_scores_by_scoring_method(
    [scores for scores in evaluation_results]
  )

def configure_pipeline(p, opt):
  xml_mapping = parse_xml_mapping(opt.xml_mapping)
  field_names = opt.fields
  output_columns = DEFAULT_OUTPUT_COLUMNS
  # read the files and create a collection with filename, content tuples
  evaluation_results = (
    p |
    beam.Create([{
      'data_path': opt.data_path,
      'prediction_suffix': opt.prediction_suffix,
      'target_suffix': opt.target_suffix
    }]) |
    "FindFilePairs" >> beam.FlatMap(FindFilePairs) |
    "LogFilePairs" >> MapSpy(lambda x: get_logger().info('out: %s', x)) |
    "ReadFilePairs" >> beam.Map(ReadFilePairs) |
    "EvaluateFilePairs" >> beam.Map(partial(
      EvaluateFilePairs,
      xml_mapping=xml_mapping,
      field_names=field_names
    ))
  )

  _ = (
    evaluation_results |
    "LogEvaluationResults" >> MapSpy(
      lambda x: get_logger().info('out: %s', x['evaluation_results'])
    ) |
    "FlattenEvaluationResults" >> beam.FlatMap(
      FlattenEvaluationResults(field_names=field_names)
    ) |
    "WriteEvaluationToCsv" >> WriteDictCsv(
      os.path.join(opt.output_path, 'results'),
      file_name_suffix='.csv',
      columns=DEFAULT_OUTPUT_COLUMNS
    )
  )

  _ = (
    evaluation_results |
    "ExtractEvaluationResults" >> beam.Map(lambda x: x['evaluation_results']) |
    "LogEvalResults" >> MapSpy(lambda x: get_logger().info('!!!!! eval out: %s', str(x)[:150])) |
    "ByScoringMethod" >> beam.Map(lambda x: scoring_method_as_top_level_key(x)) |
    "CombineResults" >> beam.CombineGlobally(
      combine_and_compact_scores_by_scoring_method
    ) |
    "LogCombinedResults" >> MapSpy(lambda x: get_logger().info('combined out: %s', str(x)[:1350])) |
    "Summarise" >> beam.Map(
      lambda x: summarise_results_by_scoring_method(x, field_names)
    ) |
    "FlattenSummary" >> beam.FlatMap(flatten_summary_results) |
    "LogSummary" >> MapSpy(lambda x: get_logger().info('summary out: %s', str(x)[:1350])) |
    "WriteSummaryToCsv" >> WriteDictCsv(
      os.path.join(opt.output_path, 'summary'),
      file_name_suffix='.csv',
      columns=DEFAULT_SUMMARY_OUTPUT_COLUMNS
    )
  )

def get_cloud_project():
  cmd = [
    'gcloud', '-q', 'config', 'list', 'project',
    '--format=value(core.project)'
  ]
  with open(os.devnull, 'w') as dev_null:
    try:
      res = subprocess.check_output(cmd, stderr=dev_null).strip()
      if not res:
        raise Exception(
          '--cloud specified but no Google Cloud Platform '
          'project found.\n'
          'Please specify your project name with the --project '
          'flag or set a default project: '
          'gcloud config set project YOUR_PROJECT_NAME'
        )
      return res
    except OSError as e:
      if e.errno == errno.ENOENT:
        raise Exception(
          'gcloud is not installed. The Google Cloud SDK is '
          'necessary to communicate with the Cloud ML service. '
          'Please install and set up gcloud.'
        )
      raise

def parse_args(argv=None):
  parser = argparse.ArgumentParser()
  parser.add_argument(
    '--data-path',
    type=str,
    required=True,
    help='path to data directory containing sub directories with target and predicted XML'
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
    '--xml-mapping',
    type=str,
    default='xml-mapping.conf',
    help='filename to the xml mapping configuration'
  )
  parser.add_argument(
    '--output-path',
    required=False,
    help='Output directory to write results to.'
  )
  parser.add_argument(
    '--output-suffix',
    required=False,
    default='.tei-header.xml',
    help='Output file suffix to add to the filename (excluding the file extension).'
  )
  parser.add_argument(
    '--fields',
    type=comma_separated_str_to_list,
    default=['abstract', 'authors', 'first_author', 'keywords', 'title'],
    help='comma separated list of fields to process'
  )
  parser.add_argument(
    '--runner',
    required=False,
    default=None,
    help='Runner.'
  )
  parser.add_argument(
    '--cloud',
    default=False,
    action='store_true'
  )
  parser.add_argument(
    '--project',
    type=str,
    help='The cloud project name to be used for running this pipeline'
  )
  parser.add_argument(
    '--num_workers',
    default=10,
    type=int,
    help='The number of workers.'
  )
  # parsed_args, other_args = parser.parse_known_args(argv)
  parsed_args = parser.parse_args(argv)

  if not parsed_args.output_path:
    reduced_data_path = parsed_args.data_path.replace('/*/', '/')
    parsed_args.output_path = os.path.join(
      os.path.dirname(reduced_data_path),
      os.path.basename(reduced_data_path + '-results')
    )
  if parsed_args.num_workers:
    parsed_args.autoscaling_algorithm = 'NONE'
    parsed_args.max_num_workers = parsed_args.num_workers
  parsed_args.setup_file = './setup.py'

  if parsed_args.cloud:
    # Flags which need to be set for cloud runs.
    default_values = {
      'project':
        get_cloud_project(),
      'temp_location':
        os.path.join(os.path.dirname(parsed_args.output_path), 'temp'),
      'runner':
        'DataflowRunner',
      'save_main_session':
        True,
    }
  else:
    # Flags which need to be set for local runs.
    default_values = {
      'runner': 'DirectiRunner',
    }

  get_logger().info('default_values: %s', default_values)
  for kk, vv in default_values.iteritems():
    if kk not in parsed_args or not vars(parsed_args)[kk]:
      vars(parsed_args)[kk] = vv
  get_logger().info('parsed_args: %s', parsed_args)

  return parsed_args

def run(argv=None):
  """Main entry point; defines and runs the tfidf pipeline."""
  known_args = parse_args(argv)

  # We use the save_main_session option because one or more DoFn's in this
  # workflow rely on global context (e.g., a module imported at module level).
  pipeline_options = PipelineOptions.from_dictionary(vars(known_args))
  pipeline_options.view_as(SetupOptions).save_main_session = True

  runner = known_args.runner
  if runner == 'FnApiRunner':
    runner = create_fn_api_runner()

  with beam.Pipeline(runner, options=pipeline_options) as p:
    configure_pipeline(p, known_args)

    # Execute the pipeline and wait until it is completed.


if __name__ == '__main__':
  logging.basicConfig(level='INFO')

  run()
