from sciencebeam_judge.evaluation.custom.deleted_text import (
    get_fuzzy_matched_text_fragments,
    DeletedTextEvaluation
)


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


class TestDeletedTextEvaluation:
    def test_should_return_one_if_all_text_was_found(self):
        match_score = DeletedTextEvaluation().score(
            expected=['value1'],
            actual=['value1']
        )
        assert match_score.score == 1.0
        assert match_score.true_positive == 1

    def test_should_return_zero_if_all_text_is_missing(self):
        match_score = DeletedTextEvaluation().score(
            expected=['value1'],
            actual=[]
        )
        assert match_score.score == 0.0
        assert match_score.false_negative == 1

    def test_should_return_dot_five_if_half_of_the_values_are_missing(self):
        match_score = DeletedTextEvaluation().score(
            expected=['value1', 'value2'],
            actual=['value1']
        )
        assert match_score.score == 0.5
        assert match_score.false_negative == 1

    def test_should_return_ignore_extra_values(self):
        match_score = DeletedTextEvaluation().score(
            expected=['value1'],
            actual=['value1', 'value2']
        )
        assert match_score.score == 1.0
        assert match_score.true_positive == 1

    def test_should_return_dot_five_if_half_of_the_value_tokens_are_missing(self):
        match_score = DeletedTextEvaluation().score(
            expected=['value1 value2'],
            actual=['value1']
        )
        assert match_score.score == 0.5
        assert match_score.false_negative == 1
