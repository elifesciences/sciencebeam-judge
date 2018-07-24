from future.utils import raise_with_traceback

from .scoring_types.scoring_types import (
  resolve_scoring_type,
  DEFAULT_SCORING_TYPE_NAME
)


class DocumentScoringProps(object):
  FIELD_NAME = 'field_name'
  SCORING_TYPE = 'scoring_type'
  SCORING_METHOD = 'scoring_method'
  MATCH_SCORE = 'match_score'


def document_score_key_fn(document_score):
  try:
    return (
      document_score[DocumentScoringProps.FIELD_NAME],
      document_score[DocumentScoringProps.SCORING_TYPE],
      document_score[DocumentScoringProps.SCORING_METHOD]
    )
  except TypeError:
    raise_with_traceback(TypeError('error while gettng key for %s' % document_score))

def document_score_key_to_props(document_score_key):
  return {
    DocumentScoringProps.FIELD_NAME: document_score_key[0],
    DocumentScoringProps.SCORING_TYPE: document_score_key[1],
    DocumentScoringProps.SCORING_METHOD: document_score_key[2]
  }

def get_field_scoring_type_name(scoring_type_by_field_map, field_name):
  if scoring_type_by_field_map is None:
    scoring_type_by_field_map = {}
  return scoring_type_by_field_map.get(
    field_name,
    scoring_type_by_field_map.get('default', DEFAULT_SCORING_TYPE_NAME)
  )

def get_field_scoring_type(scoring_type_by_field_map, field_name):
  return resolve_scoring_type(get_field_scoring_type_name(
    scoring_type_by_field_map, field_name
  ))

def score_field_as_type(
  expected, actual, scoring_type, include_values=False, measures=None, convert_to_lower=False):

  return scoring_type.score(
    expected, actual,
    include_values=include_values,
    measures=measures,
    convert_to_lower=convert_to_lower
  )

def iter_score_document_fields(
  expected, actual, scoring_type_by_field_map=None,
  include_values=False, measures=None, convert_to_lower=False):

  for field_name in expected.keys():
    scoring_type_name = get_field_scoring_type_name(scoring_type_by_field_map, field_name)
    scores_by_scoring_method = score_field_as_type(
      expected[field_name],
      actual[field_name],
      include_values=include_values,
      measures=measures,
      convert_to_lower=convert_to_lower,
      scoring_type=resolve_scoring_type(scoring_type_name)
    )
    for scoring_method, match_score in scores_by_scoring_method.items():
      yield {
        DocumentScoringProps.FIELD_NAME: field_name,
        DocumentScoringProps.SCORING_TYPE: scoring_type_name,
        DocumentScoringProps.SCORING_METHOD: scoring_method,
        DocumentScoringProps.MATCH_SCORE: match_score
      }

def score_document_fields(
  expected, actual, scoring_type_by_field_map=None,
  include_values=False, measures=None, convert_to_lower=False):

  return {
    k: score_field_as_type(
      expected[k],
      actual[k],
      include_values=include_values,
      measures=measures,
      convert_to_lower=convert_to_lower,
      scoring_type=get_field_scoring_type(scoring_type_by_field_map, k)
    )
    for k in expected.keys()
  }
