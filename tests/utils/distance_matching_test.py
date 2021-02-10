import pytest

from sciencebeam_judge.evaluation.scoring_methods import levenshtein_score

from sciencebeam_judge.utils.distance_matching import (
    DistanceMeasure,
    DistanceMatch,
    DistanceMismatch,
    get_length_based_upper_bound_score,
    get_character_count_based_upper_bound_score,
    get_distance_matches
)


DEFAULT_DISTANCE_MEASURE = DistanceMeasure(levenshtein_score)

DISTANCE_MEASURE_WITH_APPROXIMATE = DistanceMeasure(
    levenshtein_score,
    [
        get_length_based_upper_bound_score,
        get_character_count_based_upper_bound_score
    ]
)


@pytest.fixture(name='distance_measure', params=[
    DEFAULT_DISTANCE_MEASURE, DISTANCE_MEASURE_WITH_APPROXIMATE
])
def distance_measure_fixture(request):
    return request.param


class TestGetLengthBasedUpperBoundScore:
    def test_should_return_one_for_two_empty_strings(self):
        assert get_length_based_upper_bound_score('', '') == 1.0

    def test_should_return_zero_if_only_one_value_is_empty(self):
        assert get_length_based_upper_bound_score('abc', '') == 0.0
        assert get_length_based_upper_bound_score('', 'abc') == 0.0

    def test_should_return_dot_five_if_one_value_is_twice_as_long(self):
        assert get_length_based_upper_bound_score('abc', '123456') == 0.5
        assert get_length_based_upper_bound_score('123456', 'abc') == 0.5

    def test_should_return_dot_two_five_if_one_value_is_four_times_as_long(self):
        assert get_length_based_upper_bound_score('ab', '12345678') == 0.25
        assert get_length_based_upper_bound_score('12345678', 'ab') == 0.25


class TestGetCharacterCountBasedUpperBoundScore:
    def test_should_return_one_for_two_empty_strings(self):
        assert get_character_count_based_upper_bound_score('', '') == 1.0

    def test_should_return_zero_if_only_one_value_is_empty(self):
        assert get_character_count_based_upper_bound_score('abc', '') == 0.0
        assert get_character_count_based_upper_bound_score('', 'abc') == 0.0

    def test_should_return_one_if_both_values_contain_same_characters(self):
        assert get_character_count_based_upper_bound_score('abc', 'cba') == 1.0
        assert get_character_count_based_upper_bound_score('cba', 'abc') == 1.0

    def test_should_return_dot_five_if_values_contain_half_the_characters(self):
        assert get_character_count_based_upper_bound_score('abcd', 'ba') == 0.5
        assert get_character_count_based_upper_bound_score('ba', 'abcd') == 0.5

    def test_should_return_dot_five_if_values_share_half_of_the_characters(self):
        assert get_character_count_based_upper_bound_score('abcd', 'baxx') == 0.5
        assert get_character_count_based_upper_bound_score('baxx', 'abcd') == 0.5

    def test_should_return_dot_five_if_values_share_half_of_the_character_counts(self):
        assert get_character_count_based_upper_bound_score('aaab', 'bbba') == 0.5
        assert get_character_count_based_upper_bound_score('bbba', 'aaab') == 0.5


class TestGetDistanceMatches:
    def test_should_return_empty_list_for_empty_inputs(self, distance_measure: DistanceMeasure):
        assert get_distance_matches([], [], distance_measure) == []

    def test_should_return_single_item_for_single_exact_match(
        self, distance_measure: DistanceMeasure
    ):
        assert get_distance_matches(
            ['a'],
            ['a'],
            distance_measure
        ) == [
            DistanceMatch(value_1='a', value_2='a', score=1.0)
        ]

    def test_should_return_multiple_exact_matches(self, distance_measure: DistanceMeasure):
        assert get_distance_matches(
            ['a', 'b', 'c'],
            ['c', 'b', 'a'],
            distance_measure
        ) == [
            DistanceMatch(value_1='a', value_2='a', score=1.0),
            DistanceMatch(value_1='b', value_2='b', score=1.0),
            DistanceMatch(value_1='c', value_2='c', score=1.0)
        ]

    def test_should_return_single_item_with_similar_match(
        self, distance_measure: DistanceMeasure
    ):
        assert get_distance_matches(
            ['0123456789'],
            ['012345678X'],
            distance_measure
        ) == [
            DistanceMatch(
                value_1='0123456789',
                value_2='012345678X',
                score=0.9
            )
        ]

    def test_should_return_single_similar_tuple_matche(self, distance_measure: DistanceMeasure):
        tuple_1 = tuple('0123456789')
        tuple_2 = tuple('012345678X')
        assert get_distance_matches(
            [tuple_1],
            [tuple_2],
            distance_measure
        ) == [
            DistanceMatch(value_1=tuple_1, value_2=tuple_2, score=0.9)
        ]

    def test_should_return_multiple_exact_tuple_matches(
        self, distance_measure: DistanceMeasure
    ):
        assert get_distance_matches(
            [('any', 'a'), ('any', 'b'), ('any', 'c')],
            [('any', 'c'), ('any', 'b'), ('any', 'a')],
            distance_measure
        ) == [
            DistanceMatch(value_1=('any', 'a'), value_2=('any', 'a'), score=1.0),
            DistanceMatch(value_1=('any', 'b'), value_2=('any', 'b'), score=1.0),
            DistanceMatch(value_1=('any', 'c'), value_2=('any', 'c'), score=1.0)
        ]

    def test_should_return_missing_items(self, distance_measure: DistanceMeasure):
        assert get_distance_matches(
            ['a', 'b', 'x'],
            ['b', 'a'],
            distance_measure
        ) == [
            DistanceMatch(value_1='a', value_2='a', score=1.0),
            DistanceMatch(value_1='b', value_2='b', score=1.0),
            DistanceMismatch(value_1='x', value_2=None, score=0.0)
        ]

    def test_should_return_extra_items(self, distance_measure: DistanceMeasure):
        assert get_distance_matches(
            ['a', 'b'],
            ['x', 'b', 'a'],
            distance_measure
        ) == [
            DistanceMatch(value_1='a', value_2='a', score=1.0),
            DistanceMatch(value_1='b', value_2='b', score=1.0),
            DistanceMismatch(value_1=None, value_2='x', score=0.0)
        ]

    def test_should_return_closest_mismatches(self, distance_measure: DistanceMeasure):
        assert get_distance_matches(
            ['a', 'b', '*xy*'],
            ['+xy+', 'b', 'a'],
            distance_measure,
            threshold=0.8
        ) == [
            DistanceMatch(value_1='a', value_2='a', score=1.0),
            DistanceMatch(value_1='b', value_2='b', score=1.0),
            DistanceMismatch(value_1='*xy*', value_2='+xy+', score=0.5)
        ]
