class MatchScoringProps(object):
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


def get_match_score_obj_for_score(expected, actual, score, threshold=1, include_values=False):
  binary_expected = 1 if len(expected) > 0 else 0
  # actual will be a false positive (1) if it is populated but expected is not,
  # otherwise it will be positive if it meets the threshold
  binary_actual = (
    1
    if len(actual) > 0 and (binary_expected == 0 or (binary_expected == 1 and score >= threshold))
    else 0
  )
  tp = 1 if len(actual) > 0 and len(expected) > 0 and score >= threshold else 0
  tn = 1 if len(actual) == 0 and len(expected) == 0 else 0
  fp = 1 if not tp and len(actual) > 0 else 0
  fn = 1 if not tn and len(actual) == 0 else 0
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

def get_match_score_obj_for_score_fn(expected, actual, value_f, threshold=1, include_values=False):
  return get_match_score_obj_for_score(
    expected, actual,
    value_f(expected, actual),
    threshold=threshold, include_values=include_values
  )
