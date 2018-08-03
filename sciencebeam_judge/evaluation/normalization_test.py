from .normalization import (
  normalize_whitespace,
  strip_punctuation_and_whitespace,
  FULL_PUNCTUATIONS
)

class TestNormalizeWhitespace(object):
  def test_replace_line_feed_with_space(self):
    assert normalize_whitespace('a\nb') == 'a b'

  def test_replace_cr_with_space(self):
    assert normalize_whitespace('a\rb') == 'a b'

  def test_replace_tab_with_space(self):
    assert normalize_whitespace('a\tb') == 'a b'

  def test_replace_npsp_with_space(self):
    assert normalize_whitespace(u'a\u00A0b') == u'a b'

class TestStripPunctuationAndWhitespace(object):
  def test_replace_punctuation_chars(self):
    assert strip_punctuation_and_whitespace(u'a' + FULL_PUNCTUATIONS + 'b') == 'ab'
