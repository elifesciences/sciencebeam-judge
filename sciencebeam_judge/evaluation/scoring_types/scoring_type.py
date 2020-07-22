from abc import ABC, abstractmethod


class ScoringType(ABC):
    @abstractmethod
    def score(self, expected, actual, include_values=False, measures=None, convert_to_lower=False):
        pass
