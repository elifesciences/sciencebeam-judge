import logging
from typing import List

from sciencebeam_judge.evaluation.custom.deleted_text import (
    FuzzyTextFragmentMatchResult,
    get_fuzzy_matched_text_fragments,
    get_character_based_match_score_for_score,
    DeletedTextEvaluation
)

LOGGER = logging.getLogger(__name__)

TOKEN_1 = 'token1'
TOKEN_2 = 'token2'


def get_fuzz_matched_texts(result: List[FuzzyTextFragmentMatchResult]) -> List[str]:
    return [r.value_1.text for r in result]


def get_fuzz_matched_deleted_texts(
    result: List[FuzzyTextFragmentMatchResult]
) -> List[str]:
    return [
        str(r.value_1).strip() for r in result if r.value_2 is None and str(r.value_1).strip()
    ]


def get_fuzz_matched_matching_texts(
    result: List[FuzzyTextFragmentMatchResult]
) -> List[str]:
    return [str(r.value_1).strip() for r in result if r.value_2 is not None]


def get_fuzzy_matched_text_fragments_and_log_result(**kwargs):
    result = get_fuzzy_matched_text_fragments(**kwargs)
    LOGGER.debug('result: %s', result)
    return result


class TestGetFuzzyMatchedTextFragments:
    def test_should_return_complete_match(self):
        result = get_fuzzy_matched_text_fragments_and_log_result(
            expected=['value1'],
            actual=['value1']
        )
        assert len(result) == 1
        assert result[0].value_1.text == 'value1'
        assert result[0].value_2.text == 'value1'
        assert result[0].score == 1.0

    def test_should_return_mismatch(self):
        result = get_fuzzy_matched_text_fragments_and_log_result(
            expected=['abc'],
            actual=['123']
        )
        assert len(result) >= 1
        assert result[0].value_1.text == 'abc'
        assert result[0].value_2 is None
        assert result[0].score == 0.0

    def test_should_return_allow_exact_same_text_multiple_times(self):
        result = get_fuzzy_matched_text_fragments_and_log_result(
            expected=[TOKEN_1, TOKEN_1],
            actual=[TOKEN_1, TOKEN_1]
        )
        non_whitespace_results = [
            fuzzy_matched_result
            for fuzzy_matched_result in result
            if fuzzy_matched_result.value_1.text.strip()
        ]
        value_1_texts = [r.value_1.text for r in non_whitespace_results]
        value_2_texts = [r.value_2.text for r in non_whitespace_results]
        assert '\n'.join(value_1_texts) == '\n'.join([TOKEN_1, TOKEN_1])
        assert '\n'.join(value_2_texts) == '\n'.join([TOKEN_1, TOKEN_1])

    def test_should_find_deleted_character(self):
        result = get_fuzzy_matched_text_fragments_and_log_result(
            expected=['abcdef'],
            actual=['bcdef']
        )
        assert get_fuzz_matched_deleted_texts(result) == ['a']
        assert get_fuzz_matched_matching_texts(result) == ['bcdef']

    def test_should_find_multiple_deleted_character(self):
        result = get_fuzzy_matched_text_fragments_and_log_result(
            expected=['abcdef012345'],
            actual=['bcdef12345']
        )
        assert get_fuzz_matched_deleted_texts(result) == ['a', '0']
        assert get_fuzz_matched_matching_texts(result) == ['bcdef', '12345']

    def test_should_find_multiple_deleted_and_matching_character_around_long_added_text(self):
        result = get_fuzzy_matched_text_fragments_and_log_result(
            expected=['abcdef 012345'],
            actual=['bcdef xxxxxxxxx 12345']
        )
        assert get_fuzz_matched_deleted_texts(result) == ['a', '0']
        assert get_fuzz_matched_matching_texts(result) == ['bcdef', '12345']

    def test_should_matching_also_shorter_fragment(self):
        result = get_fuzzy_matched_text_fragments_and_log_result(
            expected=['abcdef 0123456789'],
            actual=['bcdef xxxxxxxxx 123456789']
        )
        assert get_fuzz_matched_deleted_texts(result) == ['a', '0']
        assert get_fuzz_matched_matching_texts(result) == ['bcdef', '123456789']

    def test_should_ignore_extra_spaces_in_actual_text(self):
        result = get_fuzzy_matched_text_fragments_and_log_result(
            expected=['abcdef 012345'],
            actual=['b c d e f  x x x x x x x x x  1 2 3 4 5']
        )
        assert get_fuzz_matched_deleted_texts(result) == ['a', '0']
        assert get_fuzz_matched_matching_texts(result) == ['bcdef', '12345']

    def test_should_ignore_extra_spaces_in_expected_text(self):
        result = get_fuzzy_matched_text_fragments_and_log_result(
            expected=['a b c d e f   0 1 2 3 4 5'],
            actual=['bcdef xxxxxxxxx 12345']
        )
        assert get_fuzz_matched_deleted_texts(result) == ['a', '0']
        assert get_fuzz_matched_matching_texts(result) == ['b c d e f', '1 2 3 4 5']

    def test_should_ignore_extra_spaces_in_expected_text_and_deleted_text(self):
        result = get_fuzzy_matched_text_fragments_and_log_result(
            expected=['a b c d e f   x x x x x x   0 1 2 3 4 5'],
            actual=['bcdef 12345']
        )
        assert get_fuzz_matched_deleted_texts(result) == ['a', 'x x x x x x   0']
        assert get_fuzz_matched_matching_texts(result) == ['b c d e f', '1 2 3 4 5']

    def test_should_not_match_individual_characters_from_added_text(self):
        result = get_fuzzy_matched_text_fragments_and_log_result(
            expected=['abcdef 012345'],
            actual=['bcdef 12345 xxxxxxxxx a 0']
        )
        assert get_fuzz_matched_deleted_texts(result) == ['a', '0']
        assert get_fuzz_matched_matching_texts(result) == ['bcdef', '12345']

    def test_should_not_match_individual_characters_between_matched_region(self):
        result = get_fuzzy_matched_text_fragments_and_log_result(
            expected=['abcdef 12345'],
            actual=['abcdf 12345 e']
        )
        assert get_fuzz_matched_deleted_texts(result) == ['e']
        assert get_fuzz_matched_matching_texts(result) == ['abcd', 'f 12345']

    def test_should_not_match_individual_characters_from_distant_regions(self):
        result = get_fuzzy_matched_text_fragments_and_log_result(
            expected=['a bcdef 01234 5'],
            actual=['bcdef 01234 xxxxxxxx a5']
        )
        assert get_fuzz_matched_deleted_texts(result) == ['a', '5']
        assert get_fuzz_matched_matching_texts(result) == ['bcdef 01234']


class TestGetCharacterBasedMatchScoreForScore:
    def test_should_calculate_correct_true_positive_for_match(self):
        match_score = get_character_based_match_score_for_score(
            score=1.0,
            expected=TOKEN_1,
            actual=TOKEN_1,
            include_values=True
        )
        assert match_score.true_positive == len(TOKEN_1)
        assert match_score.true_negative == 0
        assert match_score.false_positive == 0
        assert match_score.false_negative == 0

    def test_should_calculate_correct_false_negative_for_deleted_text(self):
        match_score = get_character_based_match_score_for_score(
            score=0.0,
            expected=TOKEN_1,
            actual=None,
            include_values=True
        )
        assert match_score.true_positive == 0
        assert match_score.true_negative == 0
        assert match_score.false_positive == 0
        assert match_score.false_negative == len(TOKEN_1)

    def test_should_calculate_correct_false_positive_for_added_text(self):
        match_score = get_character_based_match_score_for_score(
            score=0.0,
            expected=None,
            actual=TOKEN_1,
            include_values=True
        )
        assert match_score.true_positive == 0
        assert match_score.true_negative == 0
        assert match_score.false_positive == len(TOKEN_1)
        assert match_score.false_negative == 0

    def test_should_calculate_zero_true_negative_for_no_text(self):
        match_score = get_character_based_match_score_for_score(
            score=1.0,
            expected=None,
            actual=None,
            include_values=True
        )
        assert match_score.true_positive == 0
        assert match_score.true_negative == 0
        assert match_score.false_positive == 0
        assert match_score.false_negative == 0

    def test_should_ignore_whitespace(self):
        match_score = get_character_based_match_score_for_score(
            score=1.0,
            expected=' \n\t\r' + TOKEN_1,
            actual=TOKEN_1,
            include_values=True
        )
        assert match_score.true_positive == len(TOKEN_1)
        assert match_score.true_negative == 0
        assert match_score.false_positive == 0
        assert match_score.false_negative == 0


class TestDeletedTextEvaluation:
    def test_should_return_one_if_all_text_was_found(self):
        match_score = DeletedTextEvaluation().score(
            expected=[TOKEN_1],
            actual=[TOKEN_1]
        )
        assert match_score.score == 1.0
        assert match_score.true_positive == len(TOKEN_1)

    def test_should_return_zero_if_all_text_is_missing(self):
        match_score = DeletedTextEvaluation().score(
            expected=[TOKEN_1],
            actual=[]
        )
        assert match_score.score == 0.0
        assert match_score.false_negative == len(TOKEN_1)

    def test_should_return_dot_five_if_half_of_the_values_are_missing(self):
        match_score = DeletedTextEvaluation().score(
            expected=[TOKEN_1, TOKEN_2],
            actual=[TOKEN_1]
        )
        assert match_score.score == 0.5
        assert match_score.false_negative == len(TOKEN_2)
        sub_score = match_score.sub_scores[0]
        assert str(sub_score.expected_context) == '\n'.join([TOKEN_1, TOKEN_2])
        assert sub_score.actual_context is None

    def test_should_return_ignore_extra_values(self):
        match_score = DeletedTextEvaluation().score(
            expected=[TOKEN_1],
            actual=[TOKEN_1, TOKEN_2]
        )
        assert match_score.score == 1.0
        assert match_score.true_positive == len(TOKEN_1)

    def test_should_return_dot_five_if_half_of_the_value_tokens_are_missing(self):
        match_score = DeletedTextEvaluation().score(
            expected=[f'{TOKEN_1} {TOKEN_2}'],
            actual=[TOKEN_1]
        )
        assert match_score.score == 0.5
        assert match_score.false_negative == len(TOKEN_2)
