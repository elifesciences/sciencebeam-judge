from lxml.builder import E

from .xml import (
  get_text_content
)


class TestGetTextContent(object):
  def test_should_return_text_of_node(self):
    assert get_text_content(E.dummy('text')) == 'text'

  def test_should_return_text_of_text_xpath_result(self):
    assert get_text_content(E.dummy('text').xpath('text()')[0]) == 'text'

  def test_should_return_blank_for_none_node(self):
    assert get_text_content(None) == ''
