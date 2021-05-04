from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union


T_Value = Union[str, List[str]]


class MatchScoringProps:
    EXPECTED_SOMETHING = 'expected_something'
    ACTUAL_SOMETHING = 'actual_something'
    SCORE = 'score'
    TRUE_POSITIVE = 'true_positive'
    TRUE_NEGATIVE = 'true_negative'
    FALSE_POSITIVE = 'false_positive'
    FALSE_NEGATIVE = 'false_negative'
    BINARY_EXPECTED = 'binary_expected'
    BINARY_ACTUAL = 'binary_actual'
    EXPECTED = 'expected'
    ACTUAL = 'actual'
    EXPECTED_CONTEXT = 'expected_context'
    SUB_SCORES = 'sub_scores'


@dataclass
class MatchScore:  # pylint: disable=too-many-instance-attributes
    score: float
    expected_something: bool = True
    actual_something: bool = True
    true_positive: int = 0
    true_negative: int = 0
    false_positive: int = 0
    false_negative: int = 0
    binary_expected: int = 0
    binary_actual: int = 0
    expected: Optional[T_Value] = None
    actual: Optional[T_Value] = None
    expected_context: Optional[T_Value] = None
    sub_scores: Optional[List['MatchScore']] = None

    def to_dict(self) -> Dict[str, Any]:
        props = vars(self)
        if self.sub_scores:
            props = {
                **props,
                MatchScoringProps.SUB_SCORES: [
                    score.to_dict()
                    for score in self.sub_scores
                ]
            }
        return props

    @staticmethod
    def from_dict(match_score_dict: Dict[str, Any]) -> 'MatchScore':
        if match_score_dict.get(MatchScoringProps.SUB_SCORES):
            match_score_dict = {
                **match_score_dict,
                MatchScoringProps.SUB_SCORES: [
                    MatchScore.from_dict(score)
                    for score in match_score_dict[MatchScoringProps.SUB_SCORES]
                ]
            }
        return MatchScore(**match_score_dict)


def get_match_score_obj_for_score(expected, actual, score, threshold=1, include_values=False):
    binary_expected = 1 if expected else 0
    # actual will be a false positive (1) if it is populated but expected is not,
    # otherwise it will be positive if it meets the threshold
    binary_actual = (
        1
        if actual and (binary_expected == 0 or (binary_expected == 1 and score >= threshold))
        else 0
    )
    tp = 1 if actual and expected and score >= threshold else 0
    tn = 1 if not actual and not expected else 0
    fp = 1 if not tp and actual else 0
    fn = 1 if not tn and not actual else 0
    d = {
        MatchScoringProps.EXPECTED_SOMETHING: len(expected) > 0,
        MatchScoringProps.ACTUAL_SOMETHING: len(actual) > 0,
        MatchScoringProps.SCORE: score,
        MatchScoringProps.TRUE_POSITIVE: tp,
        MatchScoringProps.TRUE_NEGATIVE: tn,
        MatchScoringProps.FALSE_POSITIVE: fp,
        MatchScoringProps.FALSE_NEGATIVE: fn,
        MatchScoringProps.BINARY_EXPECTED: binary_expected,
        MatchScoringProps.BINARY_ACTUAL: binary_actual
    }
    if include_values:
        d[MatchScoringProps.EXPECTED] = expected
        d[MatchScoringProps.ACTUAL] = actual
    return d


def get_match_score_for_score(
    expected: T_Value,
    actual: T_Value,
    score: float,
    threshold: float = 1,
    include_values: bool = False
):
    return MatchScore.from_dict(get_match_score_obj_for_score(
        actual=actual, expected=expected,
        score=score, threshold=threshold,
        include_values=include_values
    ))


def get_match_score_obj_for_score_fn(expected, actual, value_f, threshold=1, include_values=False):
    return get_match_score_obj_for_score(
        expected, actual,
        value_f(expected, actual),
        threshold=threshold, include_values=include_values
    )
