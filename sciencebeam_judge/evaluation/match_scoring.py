def get_score_obj_for_score(expected, actual, score, threshold=1, include_values=False):
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
    'expected_something': len(expected) > 0,
    'actual_something': len(actual) > 0,
    'score': score,
    'true_positive': tp,
    'true_negative': tn,
    'false_positive': fp,
    'false_negative': fn,
    'binary_expected': binary_expected,
    'binary_actual': binary_actual
  }
  if include_values:
    d['expected'] = expected
    d['actual'] = actual
  return d

def score_obj(expected, actual, value_f, threshold=1, include_values=False):
  return get_score_obj_for_score(
    expected, actual,
    value_f(expected, actual),
    threshold=threshold, include_values=include_values
  )
