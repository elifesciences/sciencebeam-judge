from __future__ import division

from .scoring_methods import ScoringMethodNames

from .document_scoring import (
  score_document_fields,
  iter_score_document_fields
)

SOME_TEXT = 'test 123'

class TestScoreDocumentFields(object):
  def test_should_score_results_for_exact_match_and_partial_match(self):
    result = score_document_fields({
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

class TestIterScoreDocumentFields(object):
  def test_should_include_field_name_scoring_type_and_scoring_method(self):
    document = {
      'field': [SOME_TEXT]
    }
    result = list(iter_score_document_fields(document, document, scoring_type_by_field_map={
      'field': 'list'
    }, measures=[ScoringMethodNames.EXACT]))
    assert result[0]['field_name'] == 'field'
    assert result[0]['scoring_type'] == 'list'
    assert result[0]['scoring_method'] == ScoringMethodNames.EXACT
