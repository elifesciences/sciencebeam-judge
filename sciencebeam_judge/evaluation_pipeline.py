from __future__ import absolute_import

import argparse
import os
import logging
from io import BytesIO
from functools import partial

from six import iteritems

import apache_beam as beam
from apache_beam.io.textio import WriteToText
from apache_beam.options.pipeline_options import PipelineOptions, SetupOptions

from sciencebeam_gym.utils.collection import (
  extend_dict
)

from sciencebeam_gym.beam_utils.utils import (
  TransformAndLog,
  TransformAndCount,
  MapOrLog,
  PreventFusion
)

from sciencebeam_gym.beam_utils.csv import (
  WriteDictCsv
)

from sciencebeam_gym.beam_utils.io import (
  read_all_from_path
)

from sciencebeam_gym.beam_utils.main import (
  add_cloud_args,
  process_cloud_args,
  process_sciencebeam_gym_dep_args
)

from sciencebeam_gym.utils.file_list import (
  load_file_list
)

from sciencebeam_judge.evaluation_utils import (
  parse_xml,
  parse_xml_mapping,
  comma_separated_str_to_list
)

from sciencebeam_judge.evaluation_config import (
  parse_evaluation_config,
  get_scoring_type_by_field_map_from_config
)

from sciencebeam_judge.grobid_evaluate import (
  format_summary_by_scoring_method as format_grobid_summary
)

from .evaluation.scoring_methods import (
  ScoreMeasures,
  ALL_SCORE_MEASURES
)

from .evaluation.score_aggregation import (
  scoring_method_as_top_level_key,
  combine_and_compact_scores_by_scoring_method_with_count,
  summarise_results_by_scoring_method_with_count
)

from .evaluation.document_scoring import (
  score_document_fields
)

from .xpath_functions import register_functions

DEFAULT_EXTRACTION_FIELDS = [
  'abstract',
  'author_surnames', 'first_author_surname',
  'author_full_names', 'first_author_full_name',
  'author_aff_strings',
  'section_titles',
  # 'section_paragraphs',
  'keywords', 'title'
]

DEFAULT_SCORE_MEASURES = [
  ScoreMeasures.EXACT,
  ScoreMeasures.LEVENSHTEIN
]

def get_logger():
  return logging.getLogger(__name__)

class MetricCounters(object):
  FILE_PAIRS = 'file_pairs'
  READ_ERROR = 'read_error'

class DataProps(object):
  TARGET_FILE_URL = 'target_file'
  PREDICTION_FILE_URL = 'prediction_file'
  TARGET_CONTENT = 'target_content'
  PREDICTION_CONTENT = 'prediction_content'
  EVALUTATION_RESULTS = 'evaluation_results'

def ReadFilePairs(x):
  get_logger().info(
    'reading: target: %s, prediction: %s',
    x[DataProps.TARGET_FILE_URL], x[DataProps.PREDICTION_FILE_URL]
  )
  return extend_dict(x, {
    DataProps.TARGET_CONTENT: read_all_from_path(x[DataProps.TARGET_FILE_URL]),
    DataProps.PREDICTION_CONTENT: read_all_from_path(x[DataProps.PREDICTION_FILE_URL])
  })

def evaluate_file_pairs(
  target_filename, target_content,
  prediction_filename, prediction_content,
  xml_mapping, field_names,
  **kwargs):

  get_logger().info(
    'processing: target: %s, prediction: %s', target_filename, prediction_filename
  )
  target_xml = parse_xml(
    BytesIO(target_content),
    xml_mapping,
    fields=field_names,
    filename=target_filename
  )
  prediction_xml = parse_xml(
    BytesIO(prediction_content),
    xml_mapping,
    fields=field_names,
    filename=prediction_filename
  )
  return score_document_fields(
    target_xml, prediction_xml, include_values=True,
    **kwargs
  )

def EvaluateFilePairs(x, **kwargs):
  return extend_dict(x, {
    DataProps.EVALUTATION_RESULTS: evaluate_file_pairs(
      x[DataProps.TARGET_FILE_URL], x[DataProps.TARGET_CONTENT],
      x[DataProps.PREDICTION_FILE_URL], x[DataProps.PREDICTION_CONTENT],
      **kwargs
    )
  })

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
  DOCUMENT_COUNT = 'document_count'
  EVALUATION_METHOD = 'evaluation_method'
  FIELD_NAME = 'field_name'
  STATS_NAME = 'stats_name'
  TP = 'tp'
  FP = 'fp'
  FN = 'fn'
  TN = 'tn'
  ACCURACY = 'accuracy'
  PRECISION = 'precision'
  RECALL = 'recall'
  F1 = 'f1'

DEFAULT_SUMMARY_OUTPUT_COLUMNS = [
  SummaryOutputColumns.DOCUMENT_COUNT,
  SummaryOutputColumns.EVALUATION_METHOD,
  SummaryOutputColumns.FIELD_NAME,
  SummaryOutputColumns.STATS_NAME,
  SummaryOutputColumns.TP,
  SummaryOutputColumns.FP,
  SummaryOutputColumns.FN,
  SummaryOutputColumns.TN,
  SummaryOutputColumns.ACCURACY,
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

def flatten_summary_results(summary_by_scoring_method, field_names=None):
  C = SummaryOutputColumns
  flat_result = []
  for scoring_method, summary in iteritems(summary_by_scoring_method):
    count = summary['count']
    for field_name in (field_names or summary['by-field'].keys()):
      field_summary = summary['by-field'].get(field_name)
      if not field_summary:
        continue
      field_totals = field_summary['total']
      field_scores = field_summary['scores']
      flat_result.append({
        C.DOCUMENT_COUNT: count,
        C.EVALUATION_METHOD: scoring_method,
        C.FIELD_NAME: field_name,
        C.TP: field_totals['true_positive'],
        C.FP: field_totals['false_positive'],
        C.FN: field_totals['false_negative'],
        C.TN: field_totals['true_negative'],
        C.ACCURACY: field_scores['accuracy'],
        C.PRECISION: field_scores['precision'],
        C.RECALL: field_scores['recall'],
        C.F1: field_scores['f1']
      })
    for stats_name in ['micro', 'macro']:
      stats = summary[stats_name]
      flat_result.append({
        C.DOCUMENT_COUNT: count,
        C.EVALUATION_METHOD: scoring_method,
        C.STATS_NAME: stats_name,
        C.ACCURACY: stats['accuracy'],
        C.PRECISION: stats['precision'],
        C.RECALL: stats['recall'],
        C.F1: stats['f1']
      })
  return flat_result

def configure_pipeline(p, opt):
  xml_mapping = parse_xml_mapping(opt.xml_mapping)
  scoring_type_by_field_map = get_scoring_type_by_field_map_from_config(
    parse_evaluation_config(opt.evaluation_config)
  )
  field_names = opt.fields

  target_file_list = load_file_list(
    opt.target_file_list,
    column=opt.target_file_column,
    limit=opt.limit
  )
  prediction_file_list = load_file_list(
    opt.prediction_file_list,
    column=opt.prediction_file_column,
    limit=opt.limit
  )
  assert target_file_list
  assert len(target_file_list) == len(prediction_file_list)

  file_pairs = [{
    DataProps.TARGET_FILE_URL: target_file_url,
    DataProps.PREDICTION_FILE_URL: prediction_file_url
  } for target_file_url, prediction_file_url in zip(target_file_list, prediction_file_list)]

  get_logger().debug('file_pairs: %s', file_pairs)

  evaluate_file_pairs_fn = partial(
    EvaluateFilePairs,
    xml_mapping=xml_mapping,
    scoring_type_by_field_map=scoring_type_by_field_map,
    field_names=field_names,
    measures=opt.measures,
    convert_to_lower=opt.convert_to_lower
  )
  evaluate_file_pairs_transform = (
    beam.Map(evaluate_file_pairs_fn) if not opt.skip_errors
    else MapOrLog(evaluate_file_pairs_fn)
  )

  evaluation_results = (
    p |
    beam.Create(file_pairs) |
    "PreventFusion" >> PreventFusion() |
    "ReadFilePairs" >> TransformAndCount(
      MapOrLog(
        ReadFilePairs,
        log_fn=lambda e, v: (
          get_logger().warning(
            'caught exception (ignoring item): %s, target: %s, prediction: %s',
            e, v[DataProps.TARGET_FILE_URL], v[DataProps.PREDICTION_FILE_URL], exc_info=e
          )
        ),
        error_count=MetricCounters.READ_ERROR
      ),
      MetricCounters.FILE_PAIRS
    ) |
    "EvaluateFilePairs" >> TransformAndLog(
      evaluate_file_pairs_transform,
      log_prefix='eval out: ',
      log_value_fn=lambda x: x['evaluation_results'],
      log_level='debug'
    )
  )

  _ = (
    evaluation_results |
    "FlattenEvaluationResults" >> beam.FlatMap(
      FlattenEvaluationResults(field_names=field_names)
    ) |
    "WriteEvaluationToCsv" >> WriteDictCsv(
      os.path.join(opt.output_path, 'results'),
      file_name_suffix='.csv',
      columns=DEFAULT_OUTPUT_COLUMNS
    )
  )

  summary = (
    evaluation_results |
    "ExtractEvaluationResults" >> beam.Map(lambda x: x[DataProps.EVALUTATION_RESULTS]) |
    "ByScoringMethod" >> beam.Map(lambda x: scoring_method_as_top_level_key(x)) |
    "PairWithOne" >> beam.Map(lambda x: (x, 1)) |
    "CombineResults" >> TransformAndLog(
      beam.CombineGlobally(
        combine_and_compact_scores_by_scoring_method_with_count
      ),
      log_prefix='combined out: ',
      log_level='debug'
    ) |
    "Summarise" >> beam.Map(
      lambda x: summarise_results_by_scoring_method_with_count(x, field_names)
    )
  )

  _ = (
    summary |
    "FlattenSummary" >> TransformAndLog(
      beam.FlatMap(partial(
        flatten_summary_results,
        field_names=field_names
      )),
      log_prefix='summary out: ',
      log_level='info'
    ) |
    "WriteSummaryToCsv" >> WriteDictCsv(
      os.path.join(opt.output_path, 'summary'),
      file_name_suffix='.csv',
      columns=DEFAULT_SUMMARY_OUTPUT_COLUMNS
    )
  )

  _ = (
    summary |
    "FormatGrobidEvaluation" >> beam.Map(
      lambda x: format_grobid_summary(x, field_names)
    ) |
    "WriteGrobidFormattedEvaluation" >> WriteToText(
      os.path.join(opt.output_path, 'grobid-formatted-summary'),
      file_name_suffix='.txt'
    )
  )


def add_main_args(parser):
  source_group = parser.add_argument_group('source')
  target_source_group = source_group.add_argument_group('target source')
  target_source_group.add_argument(
    '--target-file-list', type=str, required=True,
    help='path to target csv/tsv/lst file list'
  )
  target_source_group.add_argument(
    '--target-file-column', type=str, required=False,
    default='url',
    help='csv/tsv column (ignored for plain file list)'
  )

  prediction_source_group = source_group.add_argument_group('prediction source')
  prediction_source_group.add_argument(
    '--prediction-file-list', type=str, required=True,
    help='path to prediction csv/tsv/lst file list'
  )
  prediction_source_group.add_argument(
    '--prediction-file-column', type=str, required=False,
    default='url',
    help='csv/tsv column (ignored for plain file list)'
  )

  parser.add_argument(
    '--limit', type=int, required=False,
    help='limit the number of file pairs to process'
  )

  config_group = parser.add_argument_group('config')
  config_group.add_argument(
    '--xml-mapping', type=str,
    default='xml-mapping.conf',
    help='filename to the xml mapping configuration'
  )

  config_group.add_argument(
    '--evaluation-config', type=str,
    default='evaluation.conf',
    help='filename to the evaluation configuration'
  )

  parser.add_argument(
    '--fields',
    type=comma_separated_str_to_list,
    default=DEFAULT_EXTRACTION_FIELDS,
    help='comma separated list of fields to process'
  )

  parser.add_argument(
    '--measures',
    type=comma_separated_str_to_list,
    default=DEFAULT_SCORE_MEASURES,
    help='comma separated list of measures to process (valid values: %s)' % (
      ', '.join(ALL_SCORE_MEASURES)
    )
  )

  parser.add_argument(
    '--convert-to-lower', action='store_true',
    help='convert all text to lower case'
  )

  output_group = parser.add_argument_group('output')
  output_group.add_argument(
    '--output-path', required=True,
    help='Output directory to write results to.'
  )

  skip_errors_group = parser.add_argument_group('skip errors')
  skip_errors_group.add_argument(
    '--skip-errors', dest='skip_errors', action='store_true', default=False,
    help='skip and log evaluation error'
  )
  skip_errors_group.add_argument(
    '--no-skip-errors', dest='skip_errors', action='store_false',
    help='fail on evaluation error'
  )

  parser.add_argument(
    '--debug', action='store_true', default=False,
    help='enable debug output'
  )

def parse_args(argv=None):
  parser = argparse.ArgumentParser()
  add_main_args(parser)
  add_cloud_args(parser)

  args = parser.parse_args(argv)

  if args.debug:
    logging.getLogger().setLevel('DEBUG')

  process_cloud_args(
    args, args.output_path,
    name='sciencebeam-judge'
  )
  process_sciencebeam_gym_dep_args(args)

  get_logger().info('args: %s', args)

  return args

def run(argv=None):
  register_functions()

  args = parse_args(argv)

  # We use the save_main_session option because one or more DoFn's in this
  # workflow rely on global context (e.g., a module imported at module level).
  pipeline_options = PipelineOptions.from_dictionary(vars(args))
  pipeline_options.view_as(SetupOptions).save_main_session = True

  with beam.Pipeline(args.runner, options=pipeline_options) as p:
    configure_pipeline(p, args)

    # Execute the pipeline and wait until it is completed.


if __name__ == '__main__':
  logging.basicConfig(level='INFO')

  run()
