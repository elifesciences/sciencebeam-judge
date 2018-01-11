import logging
from mock import patch, DEFAULT

import pytest

from sciencebeam_gym.beam_utils.testing import (
  BeamTest,
  TestPipeline
)

import sciencebeam_judge.evaluation_pipeline as evaluation_pipeline
from sciencebeam_judge.evaluation_pipeline import (
  configure_pipeline,
  parse_args
)


BASE_TEST_PATH = '.temp/test/evaluation-pipeline'

TARGET_FILE_LIST_PATH = 'target-file-list.csv'
PREDICTION_FILE_LIST_PATH = 'prediction-file-list.csv'

TARGET_FILE_LIST = ['file1.nxml', 'file2.nxml']
PREDICTION_FILE_LIST = ['file1.pred.xml', 'file2.pred.xml']

FILE_LIST_MAP = {
  TARGET_FILE_LIST_PATH: TARGET_FILE_LIST,
  PREDICTION_FILE_LIST_PATH: PREDICTION_FILE_LIST
}

SINGLE_FILE_LIST_MAP = {
  TARGET_FILE_LIST_PATH: TARGET_FILE_LIST[:1],
  PREDICTION_FILE_LIST_PATH: PREDICTION_FILE_LIST[:1]
}

OUTPUT_PATH = BASE_TEST_PATH + '/out'

MIN_ARGV = [
  '--target-file-list=' + TARGET_FILE_LIST_PATH,
  '--prediction-file-list=' + PREDICTION_FILE_LIST_PATH,
  '--output-path=' + OUTPUT_PATH
]

def setup_module():
  logging.basicConfig(level='DEBUG')

def get_default_args():
  return parse_args(MIN_ARGV)

def patch_conversion_pipeline(**kwargs):
  always_mock = {
    'parse_xml_mapping',
    'load_file_list',
    'read_all_from_path',
    'evaluate_file_pairs'
  }

  return patch.multiple(
    evaluation_pipeline,
    **{
      k: kwargs.get(k, DEFAULT)
      for k in always_mock
    }
  )

def load_file_list_side_effect(file_list_map):
  return lambda key, **kwargs: file_list_map[key]

def dummy_file_content(filename):
  return b'dummy file content: %s' % filename

def read_all_from_path_side_effect():
  return lambda filename, **kwargs: dummy_file_content(filename)

@pytest.mark.slow
class TestConfigurePipeline(BeamTest):
  def test_should_pass_pdf_file_list_and_limit_to_read_dict_csv_and_read_pdf_file(self):
    with patch_conversion_pipeline() as mocks:
      opt = get_default_args()
      opt.limit = 100

      mocks['load_file_list'].side_effect = load_file_list_side_effect(FILE_LIST_MAP)

      with TestPipeline() as p:
        configure_pipeline(p, opt)

      mocks['load_file_list'].assert_any_call(
        opt.target_file_list, column=opt.target_file_column, limit=opt.limit
      )
      mocks['load_file_list'].assert_any_call(
        opt.prediction_file_list, column=opt.target_file_column, limit=opt.limit
      )
      mocks['read_all_from_path'].assert_any_call(
        TARGET_FILE_LIST[0]
      )
      mocks['read_all_from_path'].assert_any_call(
        PREDICTION_FILE_LIST[0]
      )

  def test_should_pass_around_values_with_default_pipeline(self):
    with patch_conversion_pipeline() as mocks:
      opt = get_default_args()

      mocks['load_file_list'].side_effect = load_file_list_side_effect(SINGLE_FILE_LIST_MAP)
      mocks['read_all_from_path'].side_effect = read_all_from_path_side_effect()

      with TestPipeline() as p:
        configure_pipeline(p, opt)

      mocks['evaluate_file_pairs'].assert_called_with(
        TARGET_FILE_LIST[0], dummy_file_content(TARGET_FILE_LIST[0]),
        PREDICTION_FILE_LIST[0], dummy_file_content(PREDICTION_FILE_LIST[0]),
        mocks['parse_xml_mapping'].return_value,
        opt.fields
      )
