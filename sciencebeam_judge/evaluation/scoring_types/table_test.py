from __future__ import division

import logging

from .table import ORDERED_TABLE_SCORING_TYPE


LOGGING = logging.getLogger(__name__)


TABLE_1 = {
  'head': [['Column 1', 'Column 2']],
  'body': [
    ['Cell 1.1', 'Cell 1.2'],
    ['Cell 2.1', 'Cell 2.2']
  ]
}

TABLE_2 = {
  'head': [['T2 Column 1', 'T2 Column 2']],
  'body': [
    ['T2 Cell 1.1', 'T2 Cell 1.2'],
    ['T2 Cell 2.1', 'T2 Cell 2.2']
  ]
}


def _single_cell_table(value):
  return {
    'head': [],
    'body': [[value]]
  }


class TestOrderedTableScoringType(object):
  def test_should_score_single_table_for_exact_match(self):
    result = ORDERED_TABLE_SCORING_TYPE.score([TABLE_1], [TABLE_1])
    assert result['exact']['score'] == 1
    assert result['soft']['score'] == 1
    assert result['levenshtein']['score'] == 1
    assert result['ratcliff_obershelp']['score'] == 1

  def test_should_score_multiple_tables_for_exact_match(self):
    result = ORDERED_TABLE_SCORING_TYPE.score(
      [TABLE_1, TABLE_2], [TABLE_1, TABLE_2]
    )
    assert result['exact']['score'] == 1
    assert result['soft']['score'] == 1
    assert result['levenshtein']['score'] == 1
    assert result['ratcliff_obershelp']['score'] == 1

  def test_should_return_zero_score_for_all_cells_mismatch(self):
    result = ORDERED_TABLE_SCORING_TYPE.score([TABLE_1], [TABLE_2])
    assert result['exact']['score'] == 0

  def test_should_score_close_match(self):
    result = ORDERED_TABLE_SCORING_TYPE.score(
      [_single_cell_table('Very similar xyz')],
      [_single_cell_table('Very similar xy')]
    )
    assert result['exact']['score'] == 0
    assert result['levenshtein']['score'] > 0
