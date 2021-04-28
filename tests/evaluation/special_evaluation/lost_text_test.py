from sciencebeam_judge.evaluation.special_evaluation.lost_text import LostTextEvaluation


class TestLostTextEvaluation:
    def test_should_return_one_if_all_text_was_found(self):
        match_score = LostTextEvaluation().score(
            expected=['value1'],
            actual=['value1']
        )
        assert match_score.score == 1.0
        assert match_score.true_positive == 1

    def test_should_return_zero_if_all_text_is_missing(self):
        match_score = LostTextEvaluation().score(
            expected=['value1'],
            actual=[]
        )
        assert match_score.score == 0.0
        assert match_score.false_negative == 1

    def test_should_return_dot_five_half_of_the_values_is_missing(self):
        match_score = LostTextEvaluation().score(
            expected=['value1', 'value2'],
            actual=['value1']
        )
        assert match_score.score == 0.5
        assert match_score.false_negative == 1
