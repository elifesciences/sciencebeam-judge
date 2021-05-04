from abc import ABC, abstractmethod
from typing import List

from sciencebeam_judge.evaluation.match_scoring import MatchScore


class CustomEvaluation(ABC):
    @abstractmethod
    def score(
        self,
        expected: List[str],
        actual: List[str],
        include_values: bool = True
    ) -> MatchScore:
        pass
