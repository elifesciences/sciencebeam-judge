from sciencebeam_judge.evaluation.match_scoring import (
    get_match_score_obj_for_score,
    MatchScoringProps
)


TEXT_1 = 'abc'
TEXT_2 = '123'


class TestGetMatchScoreObjForScore(object):
    def test_should_count_as_tp_for_match(self):
        match_score = get_match_score_obj_for_score(TEXT_1, TEXT_1, 1.0)
        assert match_score[MatchScoringProps.TRUE_POSITIVE] == 1
        assert match_score[MatchScoringProps.FALSE_POSITIVE] == 0
        assert match_score[MatchScoringProps.FALSE_NEGATIVE] == 0
        assert match_score[MatchScoringProps.TRUE_NEGATIVE] == 0

    def test_should_count_as_fp_for_mismatch(self):
        match_score = get_match_score_obj_for_score(TEXT_1, TEXT_2, 0.0)
        assert match_score[MatchScoringProps.TRUE_POSITIVE] == 0
        assert match_score[MatchScoringProps.FALSE_POSITIVE] == 1
        assert match_score[MatchScoringProps.FALSE_NEGATIVE] == 0
        assert match_score[MatchScoringProps.TRUE_NEGATIVE] == 0

    def test_should_count_as_fp_for_no_expected_but_actual_value(self):
        match_score = get_match_score_obj_for_score('', TEXT_2, 0.0)
        assert match_score[MatchScoringProps.TRUE_POSITIVE] == 0
        assert match_score[MatchScoringProps.FALSE_POSITIVE] == 1
        assert match_score[MatchScoringProps.FALSE_NEGATIVE] == 0
        assert match_score[MatchScoringProps.TRUE_NEGATIVE] == 0

    def test_should_count_as_fn_for_expected_but_no_actual_value(self):
        match_score = get_match_score_obj_for_score(TEXT_1, '', 0.0)
        assert match_score[MatchScoringProps.TRUE_POSITIVE] == 0
        assert match_score[MatchScoringProps.FALSE_POSITIVE] == 0
        assert match_score[MatchScoringProps.FALSE_NEGATIVE] == 1
        assert match_score[MatchScoringProps.TRUE_NEGATIVE] == 0

    def test_should_count_as_tn_for_no_expected_and_no_actual_value(self):
        match_score = get_match_score_obj_for_score('', '', 1.0)
        assert match_score[MatchScoringProps.TRUE_POSITIVE] == 0
        assert match_score[MatchScoringProps.FALSE_POSITIVE] == 0
        assert match_score[MatchScoringProps.FALSE_NEGATIVE] == 0
        assert match_score[MatchScoringProps.TRUE_NEGATIVE] == 1

    def test_should_count_as_tn_for_no_expected_and_no_actual_value_with_incorrect_zero_score(self):
        match_score = get_match_score_obj_for_score('', '', 0.0)
        assert match_score[MatchScoringProps.TRUE_POSITIVE] == 0
        assert match_score[MatchScoringProps.FALSE_POSITIVE] == 0
        assert match_score[MatchScoringProps.FALSE_NEGATIVE] == 0
        assert match_score[MatchScoringProps.TRUE_NEGATIVE] == 1
