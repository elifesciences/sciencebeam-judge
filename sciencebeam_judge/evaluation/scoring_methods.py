from __future__ import division

from difflib import SequenceMatcher

import editdistance

from .normalization import (
    strip_punctuation_and_whitespace
)


class ScoringMethodNames(object):
    EXACT = 'exact'
    SOFT = 'soft'
    LEVENSHTEIN = 'levenshtein'
    RATCLIFF_OBERSHELP = 'ratcliff_obershelp'


def exact_score(expected, actual):
    return 1 if expected == actual else 0


def levenshtein_score(expected, actual):
    if not expected and not actual:
        return 1
    return 1 - (editdistance.eval(expected, actual) / max(len(expected), len(actual)))


def ratcliff_obershelp_score(expected, actual):
    return SequenceMatcher(None, expected, actual).ratio()


def IDENTITY_FN(x):
    return x


class ScoringMethod(object):
    def __init__(self, name, scoring_fn, threshold=1, preprocessing_fn=None):
        self.name = name
        self.scoring_fn = scoring_fn
        self.threshold = threshold
        self.preprocessing_fn = preprocessing_fn or IDENTITY_FN

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


def get_scoring_methods(measures=None):
    if not measures:
        measures = ALL_SCORING_METHOD_NAMES
    return [SCORING_METHODS_MAP[k] for k in measures]
