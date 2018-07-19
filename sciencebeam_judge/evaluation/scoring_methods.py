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

ALL_SCORE_MEASURES = [
  ScoringMethodNames.EXACT,
  ScoringMethodNames.SOFT,
  ScoringMethodNames.LEVENSHTEIN,
  ScoringMethodNames.RATCLIFF_OBERSHELP
]


def exact_score(expected, actual):
  return 1 if expected == actual else 0

def levenshtein_score(expected, actual):
  if len(expected) == 0 and len(actual) == 0:
    return 1
  return 1 - (editdistance.eval(expected, actual) / max(len(expected), len(actual)))

def ratcliff_obershelp_score(expected, actual):
  return SequenceMatcher(None, expected, actual).ratio()

IDENTITY_FN = lambda x: x

class ScoringMethod(object):
  def __init__(self, name, scoring_fn, threshold=1, preprocessing_fn=None):
    self.name = name
    self.scoring_fn = scoring_fn
    self.threshold = threshold
    self.preprocessing_fn = preprocessing_fn or IDENTITY_FN

class ScoringMethods(object):
  EXACT = ScoringMethod(
    ScoringMethodNames.EXACT, exact_score
  )
  SOFT = ScoringMethod(
    ScoringMethodNames.SOFT, exact_score, preprocessing_fn=strip_punctuation_and_whitespace
  )
  LEVENSHTEIN = ScoringMethod(
    ScoringMethodNames.LEVENSHTEIN, levenshtein_score, threshold=0.8
  )
  RATCLIFF_OBERSHELP = ScoringMethod(
    ScoringMethodNames.RATCLIFF_OBERSHELP, ratcliff_obershelp_score, threshold=0.95
  )

SCORING_METHODS_MAP = {
  sm.name: sm
  for sm in [
    ScoringMethods.EXACT,
    ScoringMethods.SOFT,
    ScoringMethods.LEVENSHTEIN,
    ScoringMethods.RATCLIFF_OBERSHELP
  ]
}

def get_scoring_methods(measures=None):
  if not measures:
    measures = ALL_SCORE_MEASURES
  return [SCORING_METHODS_MAP[k] for k in measures]
