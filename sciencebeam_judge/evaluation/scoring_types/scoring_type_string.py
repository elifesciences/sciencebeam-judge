from ..normalization import normalize_whitespace

from ..scoring_methods import get_scoring_methods

from ..match_scoring import score_obj


def score_list(expected, actual, include_values=False, measures=None, convert_to_lower=False):
  # sep = '\n'
  sep = ''
  expected_str = normalize_whitespace(sep.join(expected))
  actual_str = normalize_whitespace(sep.join(actual))
  if convert_to_lower:
    expected_str = expected_str.lower()
    actual_str = actual_str.lower()
  scores = {}
  scoring_methods = get_scoring_methods(measures=measures)
  for scoring_method in scoring_methods:
    scores[scoring_method.name] = score_obj(
      scoring_method.preprocessing_fn(expected_str),
      scoring_method.preprocessing_fn(actual_str),
      scoring_method.scoring_fn,
      threshold=scoring_method.threshold,
      include_values=include_values
    )
  if not scores:
    raise AttributeError('no measures calculated')
  return scores
