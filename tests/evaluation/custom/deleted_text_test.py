from sciencebeam_judge.evaluation.custom.deleted_text import (
    get_fuzzy_matched_text_fragments,
    get_character_based_match_score_for_score,
    DeletedTextEvaluation
)


TOKEN_1 = 'token1'
TOKEN_2 = 'token2'


class TestGetFuzzyMatchedTextFragments:
    def test_should_return_complete_match(self):
        result = get_fuzzy_matched_text_fragments(
            expected=['value1'],
            actual=['value1']
        )
        assert len(result) == 1
        assert result[0].value_1.text == 'value1'
        assert result[0].value_2.text == 'value1'
        assert result[0].score == 1.0

    def test_should_return_mismatch(self):
        result = get_fuzzy_matched_text_fragments(
            expected=['abc'],
            actual=['123']
        )
        assert len(result) >= 1
        assert result[0].value_1.text == 'abc'
        assert result[0].value_2 is None
        assert result[0].score == 0.0


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
