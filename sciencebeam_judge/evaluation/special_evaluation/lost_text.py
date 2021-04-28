import logging
from typing import List

from sciencebeam_judge.evaluation.math import safe_mean

from sciencebeam_judge.evaluation.scoring_methods import (
    ScoringMethodNames,
    SCORING_METHODS_MAP
)
from sciencebeam_judge.utils.distance_matching import get_distance_matches
from sciencebeam_judge.evaluation.scoring_types.list import (
    _combine_partial_match_scores
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


class LostTextEvaluation(SpecialEvaluation):
    def score(
        self,
        expected: List[str],
        actual: List[str]
    ) -> MatchScore:
        scoring_method = SCORING_METHODS_MAP[ScoringMethodNames.LEVENSHTEIN]
        score = 0.0
        result_match_score = get_match_score_for_score(
            expected=expected,
            actual=actual,
            score=score,
            include_values=True
        )
        if expected and actual:
            match_results = get_distance_matches(
                expected,
                actual,
                distance_measure=scoring_method.distance_measure
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
