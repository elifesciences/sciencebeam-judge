from __future__ import division

import logging

import pytest

from .scoring_types import (
  resolve_scoring_type,
  ScoringTypes
)


LOGGING = logging.getLogger(__name__)

class TestResolveScoringType(object):
  def test_should_return_string_scoring_type_by_default(self):
    assert resolve_scoring_type(None) == ScoringTypes.STRING

  def test_should_return_string_scoring_type_for_str_as_literal(self):
    assert resolve_scoring_type('str') == ScoringTypes.STRING
    assert resolve_scoring_type('string') == ScoringTypes.STRING

  def test_should_return_string_scoring_type_for_set_as_literal(self):
    assert resolve_scoring_type('set') == ScoringTypes.SET

  def test_should_raise_error_for_invalid_value(self):
    with pytest.raises(ValueError):
      resolve_scoring_type('other')
