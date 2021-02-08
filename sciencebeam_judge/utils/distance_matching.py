import logging

from collections import Counter
from typing import Callable, Iterable, List, NamedTuple, Set


LOGGER = logging.getLogger(__name__)


T_Distance_Function = Callable[[str, str], float]


DEFAULT_THRESHOLD = 0.5


class DistanceMeasure(T_Distance_Function):
    def __init__(
        self,
        distance_fn: T_Distance_Function,
        approximate_distance_fn_list: List[T_Distance_Function] = None
    ):
        self._distance_fn = distance_fn
        self._approximate_distance_fn_list = approximate_distance_fn_list or []

    def __repr__(self):
        return f'{type(self).__name__}({self._distance_fn}, {self._approximate_distance_fn_list})'

    def __call__(self, value_1: str, value_2: str) -> float:
        return self._distance_fn(value_1, value_2)

    @property
    def approximations(self) -> List[T_Distance_Function]:
        return self._approximate_distance_fn_list


class DistanceMatchResult(NamedTuple):
    value_1: str
    value_2: str
    score: float


class DistanceMatch(DistanceMatchResult):
    pass


class DistanceMismatch(DistanceMatchResult):
    pass


class StrWithCache(str):
    pass


def get_score_for_match_count(match_count: int, length: int):
    if length:
        return 2.0 * match_count / length
    return 1.0


def get_length_based_upper_bound_score(value_1: str, value_2: str) -> float:
    # See difflib:SequenceMatcher.real_quick_ratio
    length_1 = len(value_1)
    length_2 = len(value_2)
    max_length = max(length_1, length_2)
    if not max_length:
        return 1.0
    # can't have more matches than the number of elements in the
    # shorter sequence
    return min(length_1, length_2) / max_length


def get_character_counts(value: str, cache_attr: str = '__chrcount') -> Counter:
    if not value:
        return Counter()
    value_counts = getattr(value, cache_attr, None)
    if not value_counts:
        value_counts = Counter(value)
        try:
            setattr(value, cache_attr, value_counts)
        except AttributeError:
            pass
    return value_counts


def get_character_count_based_upper_bound_score(value_1: str, value_2: str) -> float:
    # See difflib:SequenceMatcher.quick_ratio
    max_length = max(len(value_1), len(value_2))
    if not max_length:
        return 1.0
    if value_1 == value_2:
        return 1.0
    # viewing a and b as multisets, set matches to the cardinality
    # of their intersection; this counts the number of matches
    # without regard to order, so is clearly an upper bound
    value_counts_1 = get_character_counts(value_1)
    value_counts_2 = get_character_counts(value_2)
    # counting the intersection of the counters (min of each count)
    matches = sum(
        min(count_1, value_counts_2[c])
        for c, count_1 in value_counts_1.items()
    )
    return matches / max_length


def find_best_match(
    value: str,
    other_values: List[str],
    distance_measure: DistanceMeasure,
    threshold: float = DEFAULT_THRESHOLD,
    approximate_threshold: float = None
) -> DistanceMatchResult:

    if approximate_threshold is None:
        approximate_threshold = threshold
    best_value = None
    best_score = -1.0
    remaining_other_values = other_values
    for approximate_distance_fn in distance_measure.approximations:
        remaining_other_values_with_score = sorted([
            (approximate_distance_fn(value, other_value), other_value)
            for other_value in remaining_other_values
        ], reverse=True)
        remaining_other_values = [
            other_value
            for score, other_value in remaining_other_values_with_score
            if score >= threshold
        ]
        if len(remaining_other_values_with_score) <= 1:
            break
    for other_value in remaining_other_values:
        score = distance_measure(value, other_value)
        LOGGER.debug(
            'find_best_match, value=%r, other_value=%r, score=%s',
            value, other_value, score
        )
        if score > best_score:
            best_value = other_value
            best_score = score
            if best_score == 1.0:
                break

    LOGGER.debug(
        'find_best_match, value=%r, best_value=%r, best_score=%s',
        value, best_value, best_score
    )
    if best_score >= 0.0 and best_score >= threshold:
        return DistanceMatch(value_1=value, value_2=best_value, score=best_score)
    return None


def iter_distance_matches(
    set_1: Set[str],
    set_2: Set[str],
    distance_measure: DistanceMeasure,
    threshold: float = DEFAULT_THRESHOLD,
    mismatch_threshold: float = 0.0
) -> Iterable[DistanceMatchResult]:
    set_1 = [StrWithCache(s) for s in set_1]
    set_2 = [StrWithCache(s) for s in set_2]
    unmatched_set_1 = []
    remaining_set_2 = list(set_2)
    for value_1 in set_1:
        best_match = find_best_match(
            value_1,
            remaining_set_2,
            distance_measure=distance_measure,
            threshold=threshold
        )
        if best_match:
            yield best_match
            remaining_set_2.remove(best_match.value_2)
        else:
            unmatched_set_1.append(value_1)

    for value_1 in unmatched_set_1[:len(remaining_set_2)]:
        best_match = find_best_match(
            value_1,
            remaining_set_2,
            distance_measure=distance_measure,
            threshold=mismatch_threshold
        )
        LOGGER.debug(
            'unmatched item, best match (%s), pair with expected,'
            ' expected_item=%s, matching_item=%s',
            distance_measure, value_1, best_match
        )
        if best_match:
            yield DistanceMismatch(
                value_1=value_1, value_2=best_match.value_2, score=best_match.score
            )
            unmatched_set_1.remove(value_1)
            remaining_set_2.remove(best_match.value_2)

    for value_1 in unmatched_set_1:
        yield DistanceMismatch(value_1=value_1, value_2=None, score=0.0)
    for value_2 in remaining_set_2:
        yield DistanceMismatch(value_1=None, value_2=value_2, score=0.0)


def get_distance_matches(*args, **kwargs) -> List[DistanceMatchResult]:
    return list(iter_distance_matches(*args, **kwargs))
