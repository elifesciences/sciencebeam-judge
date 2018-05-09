from lxml.builder import E

from .jats_xpath_functions import register_functions

class TestJatsXpathFunctions(object):
  class TestAuthors(object):
    def test_should_return_single_author_node(self):
      contrib = E.contrib(
        E.name(
          E('given-names', 'Tom'),
          E('surname', 'Thomson')
        )
      )
      xml = E.article(
        E.front(
          E('article-meta', E('contrib-group', contrib))
        )
      )
      register_functions()
      assert list(xml.xpath('jats-authors(.)')) == [contrib]

  class TestFullName(object):
    def test_should_return_full_name_of_single_name(self):
      xml = E.article(
        E.name(
          E('given-names', 'Tom'),
          E('surname', 'Thomson')
        )
      )
      register_functions()
      assert list(xml.xpath('jats-full-name(//name)')) == ['Tom Thomson']

    def test_should_return_full_name_of_single_contrib(self):
      xml = E.article(
        E.contrib(
          E.name(
            E('given-names', 'Tom'),
            E('surname', 'Thomson')
          )
        )
      )
      register_functions()
      assert list(xml.xpath('jats-full-name(//contrib)')) == ['Tom Thomson']

    def test_should_not_add_space_if_surname_is_missing(self):
      xml = E.article(
        E.contrib(
          E.name(
            E('given-names', 'Tom')
          )
        )
      )
      register_functions()
      assert list(xml.xpath('jats-full-name(//contrib)')) == ['Tom']

    def test_should_not_add_space_if_surname_is_empty(self):
      xml = E.article(
        E.contrib(
          E.name(
            E('given-names', 'Tom'),
            E.surname()
          )
        )
      )
      register_functions()
      assert list(xml.xpath('jats-full-name(//contrib)')) == ['Tom']

    def test_should_return_ignore_node_if_node_is_none(self):
      xml = E.article(
        E.contrib(
          E.name(
            E('given-names', 'Tom')
          )
        )
      )
      register_functions()
      assert list(xml.xpath('jats-full-name(//contrib[2])')) == []

    def test_should_return_ignore_node_without_name(self):
      xml = E.article(
        E.contrib(
          E.other(
            E('given-names', 'Tom')
          )
        )
      )
      register_functions()
      assert list(xml.xpath('jats-full-name(//contrib)')) == []
