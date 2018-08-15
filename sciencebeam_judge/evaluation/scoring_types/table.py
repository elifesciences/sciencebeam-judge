import json
import logging

from sciencebeam_gym.utils.collection import flatten

from ..match_scoring import get_match_score_obj_for_score
from ..normalization import normalize_string
from ..scoring_methods import get_scoring_methods
from .scoring_type import ScoringType

from .list import (
  score_value_as_list_using_scoring_method,
  score_value_as_list_using_match_scoring_fn
)

LOGGER = logging.getLogger(__name__)


def tables_to_str(tables):
  if not tables:
    return ''
  return json.dumps(tables)


def _get_all_rows(table):
  return table['head'] + table['body']


def _map_cells(rows, f):
  return [
    [f(cell) for cell in row]
    for row in rows
  ]


def _normalize_rows(rows, convert_to_lower):
  return _map_cells(rows, lambda cell: normalize_string(cell, convert_to_lower=convert_to_lower))


def _dummy_value_or_blank(rows):
  return 'dummy' if rows else ''


def _get_table_match_score_for_scoring_method(
  expected_rows, actual_rows, scoring_method, include_values=False):

  to_match_score = lambda score: get_match_score_obj_for_score(
    _dummy_value_or_blank(expected_rows), _dummy_value_or_blank(actual_rows),
    score, include_values=include_values
  )
  if not expected_rows and not actual_rows:
    LOGGER.debug('empty tables (expected and actual), 1.0 score')
    return to_match_score(1.0)
  if len(expected_rows) != len(actual_rows):
    LOGGER.debug(
      'number of table rows mismatch (expected: %d, actual: %d), 0.0 score',
      len(expected_rows), len(actual_rows)
    )
    return to_match_score(0.0)
  for expected_row, actual_row in zip(expected_rows, actual_rows):
    if len(expected_row) != len(actual_row):
      return to_match_score(0.0)
  return score_value_as_list_using_scoring_method(
    flatten(expected_rows), flatten(actual_rows), scoring_method,
    include_values=include_values
  )


def _get_tables_match_score_for_scoring_method_ordered(
  expected_tables_rows, actual_tables_rows,
  scoring_method,
  include_values,
  partial):

  expected_str = tables_to_str(expected_tables_rows)
  actual_str = tables_to_str(actual_tables_rows)
  return score_value_as_list_using_match_scoring_fn(
    expected_tables_rows, actual_tables_rows,
    expected_str, actual_str,
    lambda expected_item, actual_item: _get_table_match_score_for_scoring_method(
      expected_item or [],
      actual_item or [],
      scoring_method=scoring_method,
      include_values=include_values
    ),
    scoring_method.threshold,
    include_values=include_values, partial=partial
  )


def _get_rows_and_normalize_tables(tables, convert_to_lower):
  return [
    _normalize_rows(_get_all_rows(table), convert_to_lower=convert_to_lower)
    for table in tables
  ]


class OrderedTableScoringType(ScoringType):
  def __init__(self, partial=False):
    self.partial = partial

  def score(self, expected, actual, include_values=False, measures=None, convert_to_lower=False):
    LOGGER.debug('OrderedTableScoringType, score: expected=%s, actual=%s', expected, actual)
    expected_tables_rows = _get_rows_and_normalize_tables(
      expected, convert_to_lower=convert_to_lower
    )
    actual_tables_rows = _get_rows_and_normalize_tables(
      actual, convert_to_lower=convert_to_lower
    )
    scoring_methods = get_scoring_methods(measures=measures)
    scores = {
      scoring_method.name: _get_tables_match_score_for_scoring_method_ordered(
        expected_tables_rows, actual_tables_rows, scoring_method,
        include_values=include_values, partial=self.partial
      )
      for scoring_method in scoring_methods
    }
    if not scores:
      raise AttributeError('no measures calculated')
    return scores


ORDERED_TABLE_SCORING_TYPE = OrderedTableScoringType()
PARTIAL_ORDERED_TABLE_SCORING_TYPE = OrderedTableScoringType(partial=True)
