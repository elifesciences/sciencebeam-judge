import logging

from collections import Counter
from typing import Callable, Iterable, List, NamedTuple, Set, Union, T


LOGGER = logging.getLogger(__name__)


T_Distance_Function = Callable[[str, str], float]


DEFAULT_THRESHOLD = 0.5


class StrWithCache:
    def __init__(self, value: str, index: int):
        self.value = value
        self.index = index

    def __len__(self):
        return len(self.value)

    def __str__(self):
        return self.value

    def __repr__(self):
        return repr(self.value)

    def __hash__(self) -> int:
        return hash(self.value)

    def __eq__(self, other) -> bool:
        return other == self.value


T_Str = Union[str, StrWithCache]


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


class CachedDistanceMeasure(DistanceMeasure):
    def __init__(self, distance_measure: DistanceMeasure):
        super().__init__(
            distance_measure._distance_fn,
            distance_measure._approximate_distance_fn_list
        )
        self._cache = {}

    def __call__(self, value_1: T_Str, value_2: T_Str) -> float:
        key = (
            getattr(value_1, 'index', value_1),
            getattr(value_2, 'index', value_2),
        )
        score = self._cache.get(key)
        if score is None:
            score = self._distance_fn(str(value_1), str(value_2))
            self._cache[key] = score
            LOGGER.debug('saving score to cache: %r (%r, %d)', score, key, len(self._cache))
        else:
            LOGGER.debug('used cached score: %r (%r)', score, key)
        return score


class DistanceMatchResult(NamedTuple):
    value_1: str
    value_2: str
    score: float


class DistanceMatch(DistanceMatchResult):
    pass


class DistanceMismatch(DistanceMatchResult):
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


def get_character_counts(value: T_Str, cache_attr: str = '__chrcount') -> Counter:
    if not value:
        return Counter()
    value_counts = getattr(value, cache_attr, None)
    if not value_counts:
        value_counts = Counter(str(value))
        try:
            setattr(value, cache_attr, value_counts)
        except AttributeError:
            pass
    return value_counts


def get_character_count_based_upper_bound_score(value_1: T_Str, value_2: T_Str) -> float:
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


def get_first(list_: Union[List[T]]) -> T:
    return list_[0]


def find_best_match(
    value: T_Str,
    other_values: List[T_Str],
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
        # sort by approximate score descending,
        # so that we are trying the items with a higher approximate score first
        remaining_other_values_with_score = sorted(
            [
                (approximate_distance_fn(value, other_value), other_value)
                for other_value in remaining_other_values
            ],
            key=get_first,
            reverse=True
        )
        # remove all items not meeting the threshold
        remaining_other_values = [
            other_value
            for score, other_value in remaining_other_values_with_score
            if score >= threshold
        ]
        if not remaining_other_values_with_score:
            break
    for other_value in remaining_other_values:
        # calculate true score (expensive)
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
    distance_measure = CachedDistanceMeasure(distance_measure)
    set_1 = [StrWithCache(s, i) for i, s in enumerate(set_1)]
    set_2 = [StrWithCache(s, i) for i, s in enumerate(set_2)]
    unmatched_set_1 = []
    remaining_set_2 = list(set_2)

    # find best matches that meet the threshold
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

    # try to somewhat match up pairs, now below main threshold
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

    # add remaining and unmatched items separately
    for value_1 in unmatched_set_1:
        yield DistanceMismatch(value_1=value_1, value_2=None, score=0.0)
    for value_2 in remaining_set_2:
        yield DistanceMismatch(value_1=None, value_2=value_2, score=0.0)


def get_distance_matches(*args, **kwargs) -> List[DistanceMatchResult]:
    return list(iter_distance_matches(*args, **kwargs))
