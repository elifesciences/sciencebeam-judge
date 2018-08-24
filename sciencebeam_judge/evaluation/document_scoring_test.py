from __future__ import division

import logging

from sciencebeam_utils.utils.collection import groupby_to_dict

from .scoring_methods import ScoringMethodNames

from .document_scoring import (
  iter_score_document_fields,
  DocumentScoringProps
)


LOGGER = logging.getLogger(__name__)

SOME_TEXT = 'test 123'

FIELD_1 = 'field1'
FIELD_2 = 'field2'

class TestIterScoreDocumentFields(object):
  def test_should_score_results_for_exact_match_and_partial_match(self):
    result = list(iter_score_document_fields({
      FIELD_1: [SOME_TEXT],
      FIELD_2: 'a b'
    }, {
      FIELD_1: [SOME_TEXT],
      FIELD_2: 'ab'
    }))
    result_by_scoring_method_and_field_name = groupby_to_dict(result, lambda x: (
      x[DocumentScoringProps.SCORING_METHOD],
      x[DocumentScoringProps.FIELD_NAME]
    ))
    match_score_by_scoring_method_and_field_name = {
      k: v[0]['match_score'] for k, v in result_by_scoring_method_and_field_name.items()
    }
    LOGGER.debug(
      'match_score_by_scoring_method_and_field_name: %s',
      match_score_by_scoring_method_and_field_name
    )
    assert match_score_by_scoring_method_and_field_name[('exact', FIELD_1)]['score'] == 1
    assert match_score_by_scoring_method_and_field_name[('exact', FIELD_2)]['score'] == 0
    assert match_score_by_scoring_method_and_field_name[('soft', FIELD_1)]['score'] == 1
    assert match_score_by_scoring_method_and_field_name[('soft', FIELD_2)]['score'] == 1

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
