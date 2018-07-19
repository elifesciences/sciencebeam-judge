from .scoring_types import (
  resolve_scoring_type
)

def get_field_scoring_type(scoring_type_by_field_map, field_name):
  if scoring_type_by_field_map is None:
    scoring_type_by_field_map = {}
  return resolve_scoring_type(scoring_type_by_field_map.get(
    field_name,
    scoring_type_by_field_map.get('default')
  ))

def score_field_as_type(
  expected, actual, scoring_type, include_values=False, measures=None, convert_to_lower=False):

  return scoring_type.score(
    expected, actual,
    include_values=include_values,
    measures=measures,
    convert_to_lower=convert_to_lower
  )

def score_results(
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
