from lxml.builder import E

from .tei_xpath_functions import register_functions

class TestTeiXpathFunctions(object):
  class TestAuthors(object):
    def test_should_return_single_author_node(self):
      author = E.author(
        E.persName(
          E.forename('Tom'),
          E.surname('Thomson')
        )
      )
      xml = E.TEI(E.teiHeader(E.fileDesc(E.sourceDesc(E.biblStruct(E.analytic(
        author
      ))))))
      register_functions()
      assert list(xml.xpath('tei-authors(.)')) == [author]

  class TestFullName(object):
    def test_should_return_full_name_of_single_pers_name(self):
      author = E.author(
        E.persName(
          E.forename('Tom'),
          E.surname('Thomson')
        )
      )
      xml = E.TEI(E.teiHeader(E.fileDesc(E.sourceDesc(E.biblStruct(E.analytic(
        author
      ))))))
      register_functions()
      assert list(xml.xpath('tei-full-name(//persName)')) == ['Tom Thomson']

    def test_should_return_full_name_of_multiple_forenames(self):
      author = E.author(
        E.persName(
          E.forename('Tom', type='first'),
          E.forename('T', type='middle'),
          E.surname('Thomson')
        )
      )
      xml = E.TEI(E.teiHeader(E.fileDesc(E.sourceDesc(E.biblStruct(E.analytic(
        author
      ))))))
      register_functions()
      assert list(xml.xpath('tei-full-name(//persName)')) == ['Tom T Thomson']

    def test_should_return_full_name_of_single_author(self):
      author = E.author(
        E.persName(
          E.forename('Tom'),
          E.surname('Thomson')
        )
      )
      xml = E.TEI(E.teiHeader(E.fileDesc(E.sourceDesc(E.biblStruct(E.analytic(
        author
      ))))))
      register_functions()
      assert list(xml.xpath('tei-full-name(//author)')) == ['Tom Thomson']

    def test_should_not_add_space_if_surname_is_missing(self):
      author = E.author(
        E.persName(
          E.forename('Tom')
        )
      )
      xml = E.TEI(E.teiHeader(E.fileDesc(E.sourceDesc(E.biblStruct(E.analytic(
        author
      ))))))
      register_functions()
      assert list(xml.xpath('tei-full-name(//author)')) == ['Tom']

    def test_should_not_add_space_if_surname_is_empty(self):
      author = E.author(
        E.persName(
          E.forename('Tom'),
          E.surname()
        )
      )
      xml = E.TEI(E.teiHeader(E.fileDesc(E.sourceDesc(E.biblStruct(E.analytic(
        author
      ))))))
      register_functions()
      assert list(xml.xpath('tei-full-name(//author)')) == ['Tom']
