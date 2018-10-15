from lxml import etree
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

    def test_should_include_text_of_multiple_child_nodes(self):
        assert get_text_content(
            E.dummy(E.child('text1'), E.child('text2'))
        ) == 'text1text2'

    def test_should_not_include_comments(self):
        assert get_text_content(
            etree.fromstring('<root>text<!-- comment --></root>')
        ) == 'text'
