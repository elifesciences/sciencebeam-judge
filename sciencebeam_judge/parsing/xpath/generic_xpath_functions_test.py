from lxml.builder import E

from .generic_xpath_functions import register_functions


class TestGenericXpathFunctions(object):
  class TestConcatChildren(object):
    def test_should_join_two_child_elements_of_single_parent(self):
      xml = E.article(
        E.table(
          E.label('Label 1'), E.caption('Caption 1')
        )
      )
      register_functions()
      assert (
        list(xml.xpath('generic-concat-children(//table, "$label", " ", "$caption")'))
      ) == ['Label 1 Caption 1']

    def test_should_treat_child_elements_without_text_as_blank_and_strip_spaces(self):
      xml = E.article(
        E.table(
          E.label(), E.caption('Caption 1')
        )
      )
      register_functions()
      assert (
        list(xml.xpath('generic-concat-children(//table, "$label", " ", "$caption")'))
      ) == ['Caption 1']

    def test_should_treat_absent_child_elements_as_blank_and_strip_spaces(self):
      xml = E.article(
        E.table(
          E.caption('Caption 1')
        )
      )
      register_functions()
      assert (
        list(xml.xpath('generic-concat-children(//table, "$label", " ", "$caption")'))
      ) == ['Caption 1']


  class TestJoinChildren(object):
    def test_should_join_two_child_elements_of_single_parent(self):
      xml = E.article(
        E.parent(
          E.child('Text 1'),
          E.child('Text 2')
        )
      )
      register_functions()
      assert (
        list(xml.xpath('generic-join-children(//parent, "child", ", ")'))
      ) == ['Text 1, Text 2']

    def test_should_strip_space(self):
      xml = E.article(
        E.parent(
          E.child(' Text 1'),
          E.child('Text 2 ')
        )
      )
      register_functions()
      assert (
        list(xml.xpath('generic-join-children(//parent, "child", ", ")'))
      ) == ['Text 1, Text 2']

    def test_should_return_empty_string_if_no_children_are_matched(self):
      xml = E.article(
        E.parent(
          E.other('Other 1')
        )
      )
      register_functions()
      assert (
        list(xml.xpath('generic-join-children(//parent, "child", ", ")'))
      ) == ['']


  class TestTextContent(object):
    def test_should_include_text_from_children(self):
      xml = E.article(
        E.table(
          'Text 1', E.label('Label 1'), E.caption('Caption 1')
        )
      )
      register_functions()
      assert (
        list(xml.xpath('generic-text-content(//table)'))
      ) == ['Text 1Label 1Caption 1']

    def test_should_return_empty_string_if_element_contains_no_text(self):
      xml = E.article(
        E.table()
      )
      register_functions()
      assert (
        list(xml.xpath('generic-text-content(//table)'))
      ) == ['']

    def test_should_strip_text(self):
      xml = E.article(
        E.table(' Text 1 ')
      )
      register_functions()
      assert (
        list(xml.xpath('generic-text-content(//table)'))
      ) == ['Text 1']
