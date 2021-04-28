import logging
from typing import Dict, Iterable, List, Union

from sciencebeam_judge.evaluation_config import EvaluationConfig, LostTextEvaluationConfig
from sciencebeam_judge.evaluation.match_scoring import MatchScoringProps

from .scoring_types.scoring_type import ScoringType
from .scoring_types.scoring_types import (
    resolve_scoring_type,
    DEFAULT_SCORING_TYPE_NAME
)


LOGGER = logging.getLogger(__name__)


T_Value = Union[str, List[str]]
T_DocumentValues = Dict[str, T_Value]


class DocumentScoringProps:
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
    except TypeError as exc:
        raise TypeError('error while gettng key for %s' % document_score) from exc


def document_score_key_to_props(document_score_key):
    return {
        DocumentScoringProps.FIELD_NAME: document_score_key[0],
        DocumentScoringProps.SCORING_TYPE: document_score_key[1],
        DocumentScoringProps.SCORING_METHOD: document_score_key[2]
    }


def get_field_scoring_type_names(
        scoring_types_by_field_map: Dict[str, List[str]],
        field_name: str) -> List[str]:
    if scoring_types_by_field_map is None:
        scoring_types_by_field_map = {}
    return scoring_types_by_field_map.get(
        field_name,
        scoring_types_by_field_map.get('default', [DEFAULT_SCORING_TYPE_NAME])
    )


def score_field_as_type(
        expected,
        actual,
        scoring_type: ScoringType,
        include_values: bool = False,
        measures: List[str] = None,
        convert_to_lower: bool = False):

    return scoring_type.score(
        expected, actual,
        include_values=include_values,
        measures=measures,
        convert_to_lower=convert_to_lower
    )


def iter_score_document_fields(
        expected,
        actual,
        scoring_types_by_field_map: Dict[str, List[str]] = None,
        field_names: List[str] = None,
        include_values: bool = False,
        measures: List[str] = None,
        convert_to_lower: bool = False):

    if field_names is None:
        field_names = sorted(expected.keys())

    for field_name in field_names:
        scoring_type_names = get_field_scoring_type_names(
            scoring_types_by_field_map, field_name
        )
        for scoring_type_name in scoring_type_names:
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


def iter_score_lost_text(
    expected: T_DocumentValues,
    actual: T_DocumentValues,
    lost_text_evaluation_config: LostTextEvaluationConfig
) -> Iterable[dict]:
    LOGGER.debug('lost_text_evaluation_config: %s', lost_text_evaluation_config)
    for field in lost_text_evaluation_config.fields:
        yield {
            DocumentScoringProps.FIELD_NAME: field.name,
            DocumentScoringProps.SCORING_TYPE: 'lost_text',
            DocumentScoringProps.SCORING_METHOD: 'lost_text',
            DocumentScoringProps.MATCH_SCORE: {
                MatchScoringProps.EXPECTED: expected,
                MatchScoringProps.ACTUAL: actual,
                MatchScoringProps.TRUE_POSITIVE: 1,
                MatchScoringProps.TRUE_NEGATIVE: 0,
                MatchScoringProps.FALSE_POSITIVE: 0,
                MatchScoringProps.FALSE_NEGATIVE: 0
            }
        }


def iter_score_document_fields_using_config(
    expected: T_DocumentValues,
    actual: T_DocumentValues,
    evaluation_config: EvaluationConfig,
    **kwargs
):
    LOGGER.debug('evaluation_config: %s', evaluation_config)
    yield from iter_score_document_fields(
        expected, actual,
        **kwargs
    )
    if evaluation_config.lost_text:
        yield from iter_score_lost_text(
            expected, actual,
            evaluation_config.lost_text
        )
