from typing import List

from sciencebeam_judge.evaluation.special_evaluation import SpecialEvaluation
from sciencebeam_judge.evaluation.match_scoring import MatchScore


class LostTextEvaluation(SpecialEvaluation):
    def score(
        self,
        expected: List[str],
        actual: List[str]
    ) -> MatchScore:
        return MatchScore(
            expected=expected,
            actual=actual,
            true_positive=1,
            true_negative=0,
            false_positive=0,
            false_negative=0,
            score=1.0
        )
