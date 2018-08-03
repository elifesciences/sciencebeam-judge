from io import StringIO

from .evaluation_config import (
  parse_evaluation_config,
  get_scoring_type_by_field_map_from_config
)

class TestParseEvaluationConfig(object):
  def test_should_parse_config(self):
    config_content = u'\n'.join([
      '[scoring_type]',
      'default = set',
      'title = string'
    ])
    result = parse_evaluation_config(StringIO(config_content))
    assert result == {
      'scoring_type': {
        'default': 'set',
        'title': 'string'
      }
    }

class TestGetScoringTypeByFieldMapFromConfig(object):
  def test_should_return_scoring_type_map(self):
    assert get_scoring_type_by_field_map_from_config({
      'scoring_type': {
        'default': 'set',
        'title': 'string'
      }
    }) == {
      'default': 'set',
      'title': 'string'
    }
