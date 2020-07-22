from sciencebeam_judge.evaluation.scoring_types.items import (
    _get_exact_matched_characters,
    _get_fuzzy_matched_characters,
    _score_items_to
)


UNICODE_CHAR = u'\u2013'
UNICODE_STR = u'Unicode %s' % UNICODE_CHAR


class TestGetExactMatchedCharacters:
    def test_should_match_all_characters(self):
        assert _get_exact_matched_characters('abc', ['ab', 'c']) == [True] * 3

    def test_should_match_some_characters(self):
        assert _get_exact_matched_characters('abc', ['ab', 'd']) == [
            True, True, False
        ]

    def test_should_ignore_empty_needles(self):
        assert _get_exact_matched_characters('abc', ['']) == [False] * 3

    def test_should_not_fail_on_empty_haystack(self):
        assert _get_exact_matched_characters('', ['abc']) == []


class TestGetFuzzyMatchedCharacters:
    def test_should_match_all_characters(self):
        assert _get_fuzzy_matched_characters(
            'abc', ['ab', 'c'], threshold=1
        ) == [True] * 3

    def test_should_match_some_characters(self):
        assert _get_fuzzy_matched_characters('abc', ['ab', 'd'], threshold=1) == [
            True, True, False
        ]

    def test_should_fuzzy_match_characters_above_threshold(self):
        assert _get_fuzzy_matched_characters('abc', ['abd'], threshold=0.5) == [
            True, True, False
        ]

    def test_should_not_fuzzy_match_characters_below_threshold(self):
        assert _get_fuzzy_matched_characters(
            'abc', ['abd'], threshold=0.9
        ) == [False] * 3

    def test_should_fuzzy_match_unicode_characters(self):
        assert _get_fuzzy_matched_characters(
            UNICODE_STR, [UNICODE_STR], threshold=0.9
        ) == [True] * len(UNICODE_STR)

    def test_should_ignore_empty_needles(self):
        assert _get_fuzzy_matched_characters(
            'abc', [''], threshold=0.9
        ) == [False] * 3

    def test_should_not_fail_on_empty_haystack(self):
        assert _get_fuzzy_matched_characters('', ['abc'], threshold=0.9) == []


class TestScoreItemsTo:
    def test_should_return_zero_for_empty_haystack_not_empty_needles(self):
        assert _score_items_to([], ['abc'], lambda *_: []) == 0.0

    def test_should_return_zero_for_non_empty_haystack_empty_needles(self):
        assert _score_items_to(['abc'], [], lambda *_: [False] * 3) == 0.0

    def test_should_return_one_for_empty_haystack_and_needles(self):
        assert _score_items_to([], [], lambda *_: []) == 1.0

    def test_should_return_one_for_haystack_and_needles_containing_empty_string(self):
        assert _score_items_to([''], [''], lambda *_: []) == 1.0
