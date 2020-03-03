from __future__ import division

import logging

import pytest

from sciencebeam_judge.evaluation.scoring_types.list import (
    ORDERED_LIST_SCORING_TYPE,
    UNORDERED_LIST_SCORING_TYPE,
    SET_SCORING_TYPE
)
from sciencebeam_judge.evaluation.scoring_types.string import STRING_SCORING_TYPE

from sciencebeam_judge.evaluation.scoring_types.scoring_types import resolve_scoring_type


LOGGING = logging.getLogger(__name__)


class TestResolveScoringType(object):
    def test_should_return_string_scoring_type_by_default(self):
        assert resolve_scoring_type(None) == STRING_SCORING_TYPE

    def test_should_return_string_scoring_type_for_str_as_literal(self):
        assert resolve_scoring_type('str') == STRING_SCORING_TYPE
        assert resolve_scoring_type('string') == STRING_SCORING_TYPE

    def test_should_return_string_scoring_type_for_list_as_literal(self):
        assert resolve_scoring_type('list') == ORDERED_LIST_SCORING_TYPE

    def test_should_return_string_scoring_type_for_ulist_as_literal(self):
        assert resolve_scoring_type('ulist') == UNORDERED_LIST_SCORING_TYPE

    def test_should_return_string_scoring_type_for_set_as_literal(self):
        assert resolve_scoring_type('set') == SET_SCORING_TYPE

    def test_should_raise_error_for_invalid_value(self):
        with pytest.raises(ValueError):
            resolve_scoring_type('other')
