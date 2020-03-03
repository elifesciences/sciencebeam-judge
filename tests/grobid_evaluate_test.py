from sciencebeam_judge.evaluation.scoring_methods import ScoringMethodNames
from sciencebeam_judge.evaluation.scoring_types.scoring_types import ScoringTypeNames
from sciencebeam_judge.evaluation.document_scoring import DocumentScoringProps
from sciencebeam_judge.evaluation.score_aggregation import SummaryScoresProps

from sciencebeam_judge.grobid_evaluate import (
    summarised_document_scores_to_scores_by_scoring_method,
    format_summary_by_scoring_method,
    format_summarised_document_scores_as_grobid_report
)


FIELD_1 = 'field1'

SCORE_FIELDS = ['accuracy', 'precision', 'recall', 'f1']

SCORES = {k: 1.0 for k in SCORE_FIELDS}

FIELD_SCORES = SCORES
MICRO_SCORES = SCORES
MACRO_SCORES = SCORES

SUMMARY_SCORES = {
    'by-field': {
        FIELD_1: {
            'scores': SCORES
        }
    },
    'micro': MICRO_SCORES,
    'macro': MACRO_SCORES
}

FIELD_1_REPORT = (
    '''
  ======= Strict Matching ======= (exact matches)

  ===== Field-level results =====

                 label   accuracy  precision     recall         f1

              field1     100.00     100.00     100.00     100.00

          all fields     100.00     100.00     100.00     100.00      (micro average)
              100.00     100.00     100.00     100.00 (macro average)
    '''
)


def _normalize_report(s):
    return s.replace('  ', ' ').strip()


class TestSummarisedDocumentScoresToScoresByScoringMethod(object):
    def test_should_convert_single_summary_score(self):
        summarised_document_scores = [{
            DocumentScoringProps.FIELD_NAME: FIELD_1,
            DocumentScoringProps.SCORING_METHOD: ScoringMethodNames.EXACT,
            DocumentScoringProps.SCORING_TYPE: ScoringTypeNames.STRING,
            SummaryScoresProps.SUMMARY_SCORES: SUMMARY_SCORES
        }]
        expected_scores_by_scoring_method = {
            ScoringMethodNames.EXACT: SUMMARY_SCORES
        }
        actual_scores_by_scoring_method = summarised_document_scores_to_scores_by_scoring_method(
            summarised_document_scores
        )
        assert actual_scores_by_scoring_method == expected_scores_by_scoring_method

    def test_should_ignore_summary_scores_without_string_scoring_type(self):
        summarised_document_scores = [{
            DocumentScoringProps.FIELD_NAME: FIELD_1,
            DocumentScoringProps.SCORING_METHOD: ScoringMethodNames.EXACT,
            DocumentScoringProps.SCORING_TYPE: ScoringTypeNames.LIST,
            SummaryScoresProps.SUMMARY_SCORES: SUMMARY_SCORES
        }]
        expected_scores_by_scoring_method = {
        }
        actual_scores_by_scoring_method = summarised_document_scores_to_scores_by_scoring_method(
            summarised_document_scores
        )
        assert actual_scores_by_scoring_method == expected_scores_by_scoring_method


class TestFormatSummaryByScoringMethod(object):
    def test_should_not_end_with_space(self):
        scores_by_scoring_method = {
            ScoringMethodNames.EXACT: SUMMARY_SCORES
        }
        assert not format_summary_by_scoring_method(
            scores_by_scoring_method, [FIELD_1]
        ).endswith(' ')


class TestFormatSummarisedDocumentScoresAsGrobidReport(object):
    def test_should_generate_report_for_single_field(self):
        summarised_document_scores = [{
            DocumentScoringProps.FIELD_NAME: FIELD_1,
            DocumentScoringProps.SCORING_METHOD: ScoringMethodNames.EXACT,
            DocumentScoringProps.SCORING_TYPE: ScoringTypeNames.STRING,
            SummaryScoresProps.SUMMARY_SCORES: SUMMARY_SCORES
        }]
        result = format_summarised_document_scores_as_grobid_report(
            summarised_document_scores, [FIELD_1]
        )
        assert _normalize_report(result) == _normalize_report(FIELD_1_REPORT)
