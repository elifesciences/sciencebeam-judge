from __future__ import division

import logging
from unittest.mock import patch, MagicMock
from typing import Iterable

import pytest

from sciencebeam_utils.utils.collection import groupby_to_dict

from sciencebeam_judge.evaluation_config import (
    DeletedTextFieldExpectedActualEvaluationConfig,
    DeletedTextFieldEvaluationConfig,
    DeletedTextEvaluationConfig
)

from sciencebeam_judge.evaluation.scoring_methods import ScoringMethodNames
from sciencebeam_judge.evaluation.match_scoring import MatchScore

import sciencebeam_judge.evaluation.document_scoring as document_scoring_module
from sciencebeam_judge.evaluation.document_scoring import (
    iter_score_document_fields,
    iter_score_lost_text,
    DocumentScoringProps,
    DocumentFieldScore
)


LOGGER = logging.getLogger(__name__)

SOME_TEXT = 'test 123'

FIELD_1 = 'field1'
FIELD_2 = 'field2'


SCORING_DOCUMENT_1 = {
    'field': [SOME_TEXT]
}

MATCH_SCORE_1 = MatchScore(score=0.91)


@pytest.fixture(name='lost_text_evaluation_class_mock')
def _lost_text_evaluation_class_mock() -> Iterable[MagicMock]:
    with patch.object(document_scoring_module, 'DeletedTextEvaluation') as mock:
        yield mock


@pytest.fixture(name='lost_text_evaluation_mock')
def _lost_text_evaluation_mock(lost_text_evaluation_class_mock: MagicMock) -> MagicMock:
    return lost_text_evaluation_class_mock.return_value


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


class TestIterScoreDeletedText:
    def test_should_skip_without_any_fields(self):
        result = list(iter_score_lost_text(
            SCORING_DOCUMENT_1, SCORING_DOCUMENT_1,
            DeletedTextEvaluationConfig(fields=[])
        ))
        assert result == []

    def test_should_return_one_if_all_text_was_found(
        self,
        lost_text_evaluation_mock: MagicMock
    ):
        lost_text_evaluation_mock.score.return_value = MATCH_SCORE_1
        expected_document = {'expected': ['expected1']}
        actual_document = {'actual': ['actual1']}
        result = list(map(DocumentFieldScore.from_dict, iter_score_lost_text(
            expected_document, actual_document,
            DeletedTextEvaluationConfig(fields=[
                DeletedTextFieldEvaluationConfig(
                    name=FIELD_1,
                    expected=DeletedTextFieldExpectedActualEvaluationConfig(
                        field_names=['expected']
                    ),
                    actual=DeletedTextFieldExpectedActualEvaluationConfig(
                        field_names=['actual']
                    )
                )
            ])
        )))
        assert [r.field_name for r in result] == [FIELD_1]
        assert [r.scoring_type for r in result] == ['deleted_text']
        assert [r.scoring_method for r in result] == ['deleted_text']
        assert result[0].match_score == MATCH_SCORE_1
        lost_text_evaluation_mock.score.assert_called_with(
            expected=['expected1'],
            actual=['actual1']
        )
