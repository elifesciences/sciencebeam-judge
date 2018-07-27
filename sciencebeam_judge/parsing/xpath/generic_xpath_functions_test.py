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
