from typing import List

from sciencebeam_judge.evaluation.special_evaluation import SpecialEvaluation
from sciencebeam_judge.evaluation.match_scoring import MatchScore, get_match_score_for_score


class LostTextEvaluation(SpecialEvaluation):
    def score(
        self,
        expected: List[str],
        actual: List[str]
    ) -> MatchScore:
        score = 0.0
        if expected == actual:
            score = 1.0
        return get_match_score_for_score(
            expected=expected,
            actual=actual,
            score=score,
            include_values=True
        )
