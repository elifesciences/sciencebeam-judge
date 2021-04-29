import logging
from typing import List, NamedTuple

from sciencebeam_judge.evaluation.math import safe_mean

from sciencebeam_judge.evaluation.scoring_types.list import (
    _combine_partial_match_scores
)
from sciencebeam_judge.evaluation.scoring_types.items import (
    _get_fuzzy_matched_characters
)

from sciencebeam_judge.evaluation.special_evaluation import SpecialEvaluation
from sciencebeam_judge.evaluation.match_scoring import MatchScore, get_match_score_for_score


LOGGER = logging.getLogger(__name__)


def combine_partial_match_scores(
    scores: List[MatchScore],
    template_score: MatchScore
):
    return MatchScore.from_dict(_combine_partial_match_scores(
        [score.to_dict() for score in scores],
        template_score.to_dict()
    ))


class TextFragment(NamedTuple):
    text: str


class FuzzyTextFragmentMatchResult(NamedTuple):
    value_1: TextFragment
    value_2: TextFragment
    score: float


def get_fuzzy_matched_text_fragments(
    expected: List[str],
    actual: List[str]
) -> List[FuzzyTextFragmentMatchResult]:
    haystack_str = '\n'.join(expected)
    needles = actual
    threshold = 0.5
    if not haystack_str:
        return []
    haystack_matched = _get_fuzzy_matched_characters(
        haystack_str=haystack_str,
        needles=needles,
        threshold=threshold
    )
    match_start_index = 0
    mismatch_start_index = 0
    result = []
    for index, is_match in enumerate(haystack_matched):
        if is_match:
            if mismatch_start_index < index:
                text_fragment = TextFragment(text=haystack_str[mismatch_start_index:index])
                result.append(FuzzyTextFragmentMatchResult(
                    value_1=text_fragment,
                    value_2=None,
                    score=0.0
                ))
            mismatch_start_index = index + 1
            continue
        if match_start_index < index:
            text_fragment = TextFragment(text=haystack_str[match_start_index:index])
            result.append(FuzzyTextFragmentMatchResult(
                value_1=text_fragment,
                value_2=text_fragment,
                score=1.0
            ))
        match_start_index = index + 1
    if mismatch_start_index < len(haystack_str):
        text_fragment = TextFragment(text=haystack_str[mismatch_start_index:])
        result.append(FuzzyTextFragmentMatchResult(
            value_1=text_fragment,
            value_2=None,
            score=0.0
        ))
    if match_start_index < len(haystack_str):
        text_fragment = TextFragment(text=haystack_str[match_start_index:])
        result.append(FuzzyTextFragmentMatchResult(
            value_1=text_fragment,
            value_2=text_fragment,
            score=1.0
        ))
    return result


class DeletedTextEvaluation(SpecialEvaluation):
    def score(
        self,
        expected: List[str],
        actual: List[str]
    ) -> MatchScore:
        # scoring_method = SCORING_METHODS_MAP[ScoringMethodNames.LEVENSHTEIN]
        score = 0.0
        result_match_score = get_match_score_for_score(
            expected=expected,
            actual=actual,
            score=score,
            include_values=True
        )
        if expected and actual:
            match_results = get_fuzzy_matched_text_fragments(
                expected,
                actual
            )
            LOGGER.debug('match_results: %s', match_results)
            match_scores: List[MatchScore] = []
            for match_result in match_results:
                if not match_result.value_1:
                    # ignore extra text
                    continue
                match_scores.append(get_match_score_for_score(
                    score=match_result.score,
                    expected=match_result.value_1 or '',
                    actual=match_result.value_2 or ''
                ))
            result_match_score.score = safe_mean([
                _score.score for _score in match_scores
            ]) if match_scores else 1.0
            result_match_score = combine_partial_match_scores(
                match_scores,
                result_match_score
            )
        LOGGER.debug('result_match_score: %s', result_match_score)
        return result_match_score
