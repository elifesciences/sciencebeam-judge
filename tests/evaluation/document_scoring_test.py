from __future__ import division

import logging

from sciencebeam_utils.utils.collection import groupby_to_dict

from sciencebeam_judge.evaluation_config import (
    LostTextFieldExpectedActualEvaluationConfig,
    LostTextFieldEvaluationConfig,
    LostTextEvaluationConfig
)

from sciencebeam_judge.evaluation.match_scoring import MatchScoringProps
from sciencebeam_judge.evaluation.scoring_methods import ScoringMethodNames

from sciencebeam_judge.evaluation.document_scoring import (
    iter_score_document_fields,
    iter_score_lost_text,
    DocumentScoringProps
)


LOGGER = logging.getLogger(__name__)

SOME_TEXT = 'test 123'

FIELD_1 = 'field1'
FIELD_2 = 'field2'


SCORING_DOCUMENT_1 = {
    'field': [SOME_TEXT]
}


class TestIterScoreDocumentFields:
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
        assert match_score_by_scoring_method_and_field_name[(
            'exact', FIELD_1
        )]['score'] == 1
        assert match_score_by_scoring_method_and_field_name[(
            'exact', FIELD_2
        )]['score'] == 0
        assert match_score_by_scoring_method_and_field_name[(
            'soft', FIELD_1
        )]['score'] == 1
        assert match_score_by_scoring_method_and_field_name[(
            'soft', FIELD_2
        )]['score'] == 1

    def test_should_include_field_name_scoring_type_and_scoring_method(self):
        document = {
            'field': [SOME_TEXT]
        }
        result = list(iter_score_document_fields(document, document, scoring_types_by_field_map={
            'field': ['list']
        }, measures=[ScoringMethodNames.EXACT]))
        assert result[0]['field_name'] == 'field'
        assert result[0]['scoring_type'] == 'list'
        assert result[0]['scoring_method'] == ScoringMethodNames.EXACT

    def test_should_allow_multiple_scoring_types(self):
        document = {
            'field': [SOME_TEXT]
        }
        result = list(iter_score_document_fields(document, document, scoring_types_by_field_map={
            'field': ['list', 'set']
        }, measures=[ScoringMethodNames.EXACT]))
        assert [r['field_name'] for r in result] == ['field', 'field']
        assert [r['scoring_type'] for r in result] == ['list', 'set']


class TestIterScoreLostText:
    def test_should_skip_without_any_fields(self):
        result = list(iter_score_lost_text(
            SCORING_DOCUMENT_1, SCORING_DOCUMENT_1,
            LostTextEvaluationConfig(fields=[])
        ))
        assert result == []

    def test_should_return_one_if_all_text_was_found(self):
        result = list(iter_score_lost_text(
            SCORING_DOCUMENT_1, SCORING_DOCUMENT_1,
            LostTextEvaluationConfig(fields=[
                LostTextFieldEvaluationConfig(
                    name=FIELD_1,
                    expected=LostTextFieldExpectedActualEvaluationConfig(
                        field_names=['expected1']
                    ),
                    actual=LostTextFieldExpectedActualEvaluationConfig(
                        field_names=['actual1']
                    )
                )
            ])
        ))
        assert [r[DocumentScoringProps.FIELD_NAME] for r in result] == [FIELD_1]
        assert [r[DocumentScoringProps.SCORING_TYPE] for r in result] == ['lost_text']
        assert [r[DocumentScoringProps.SCORING_METHOD] for r in result] == ['lost_text']
        match_score = result[0][DocumentScoringProps.MATCH_SCORE]
        assert match_score
        assert match_score[MatchScoringProps.TRUE_POSITIVE] == 1
