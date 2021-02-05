from __future__ import division
from functools import wraps
from typing import Callable, List

from difflib import SequenceMatcher

import editdistance

from ..utils.distance_matching import (
    T_Distance_Function,
    DistanceMeasure
)

from .normalization import (
    strip_punctuation_and_whitespace
)


class ScoringMethodNames:
    EXACT = 'exact'
    SOFT = 'soft'
    LEVENSHTEIN = 'levenshtein'
    RATCLIFF_OBERSHELP = 'ratcliff_obershelp'


def exact_score(expected: str, actual: str) -> float:
    return 1 if expected == actual else 0


def levenshtein_score(expected: str, actual: str) -> float:
    if not expected and not actual:
        return 1
    return 1 - (editdistance.eval(expected, actual) / max(len(expected), len(actual)))


def ratcliff_obershelp_score(expected: str, actual: str) -> float:
    return SequenceMatcher(None, expected, actual).ratio()


def IDENTITY_FN(x):
    return x


def wrap_scoring_function_with_preprocessing(
    scoring_fn: T_Distance_Function,
    preprocessing_fn: Callable[[str], str]
) -> T_Distance_Function:
    if preprocessing_fn is None or (preprocessing_fn == IDENTITY_FN):  # noqa pylint: disable=comparison-with-callable
        return scoring_fn

    @wraps(scoring_fn)
    def wrapped(value_1: str, value_2: str) -> float:
        if value_1:
            value_1 = preprocessing_fn(value_1)
        if value_2:
            value_2 = preprocessing_fn(value_2)
        return scoring_fn(value_1, value_2)
    return wrapped


class ScoringMethod:
    def __init__(
            self,
            name: str,
            scoring_fn: T_Distance_Function,
            threshold: float = 1,
            preprocessing_fn: Callable[[str], str] = None):
        self.name = name
        self.scoring_fn = scoring_fn
        self.threshold = threshold
        self.preprocessing_fn = preprocessing_fn or IDENTITY_FN

    def wrap_with_preprocessing(
        self,
        scoring_fn: T_Distance_Function
    ) -> T_Distance_Function:
        return wrap_scoring_function_with_preprocessing(
            scoring_fn,
            self.preprocessing_fn
        )

    @property
    def distance_measure(self) -> DistanceMeasure:
        return DistanceMeasure(
            self.wrap_with_preprocessing(self.scoring_fn)
        )

    def __str__(self):
        return self.name

    def __repr__(self):
        return '%s(threshold=%.3f)' % (self.name, self.threshold)


SCORING_METHODS = [
    ScoringMethod(
        ScoringMethodNames.EXACT, exact_score
    ),
    ScoringMethod(
        ScoringMethodNames.SOFT, exact_score, preprocessing_fn=strip_punctuation_and_whitespace
    ),
    ScoringMethod(
        ScoringMethodNames.LEVENSHTEIN, levenshtein_score, threshold=0.8
    ),
    ScoringMethod(
        ScoringMethodNames.RATCLIFF_OBERSHELP, ratcliff_obershelp_score, threshold=0.95
    )
]

ALL_SCORING_METHOD_NAMES = [
    sm.name for sm in SCORING_METHODS
]

SCORING_METHODS_MAP = {
    sm.name: sm for sm in SCORING_METHODS
}


def get_scoring_methods(measures: List[str] = None) -> List[ScoringMethod]:
    if not measures:
        measures = ALL_SCORING_METHOD_NAMES
    return [SCORING_METHODS_MAP[k] for k in measures]
