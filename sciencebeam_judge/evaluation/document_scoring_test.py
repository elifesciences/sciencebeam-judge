from __future__ import division

from .document_scoring import (
  score_results
)

SOME_TEXT = 'test 123'

class TestScoreResults(object):
  def test_should_score_results_for_exact_match_and_partial_match(self):
    result = score_results({
      '_exact': [SOME_TEXT],
      '_partial': 'a b'
    }, {
      '_exact': [SOME_TEXT],
      '_partial': 'ab'
    })
    assert result['_exact']['exact']['score'] == 1
    assert result['_exact']['soft']['score'] == 1
    assert result['_partial']['exact']['score'] == 0
    assert result['_partial']['soft']['score'] == 1
