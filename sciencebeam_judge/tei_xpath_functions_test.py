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

  class TestAffString(object):
    def test_should_return_org_name(self):
      xml = E.TEI(
        E.affiliation(
          E.orgName('Department 1', type="department")
        )
      )
      register_functions()
      assert list(xml.xpath('tei-aff-string(//affiliation)')) == ['Department 1']

    def test_should_join_multiple_org_names(self):
      xml = E.TEI(
        E.affiliation(
          E.orgName('Department 1', type="department"),
          E.orgName('Institution 1', type="institution")
        )
      )
      register_functions()
      assert list(xml.xpath('tei-aff-string(//affiliation)')) == ['Department 1, Institution 1']

    def test_should_join_institution_with_postcode_settlement_country(self):
      xml = E.TEI(
        E.affiliation(
          E.orgName('Department 1', type="department"),
          E.address(
            E.postCode('Post Code 1'),
            E.settlement('Settlement 1'),
            E.country('Country 1')
          )
        )
      )
      register_functions()
      assert (
        list(xml.xpath('tei-aff-string(//affiliation)')) ==
        ['Department 1, Post Code 1, Settlement 1, Country 1']
      )

    def test_should_join_institution_with_addr_line(self):
      xml = E.TEI(
        E.affiliation(
          E.orgName('Department 1', type="department"),
          E.address(
            E.addrLine('Addr Line 1')
          )
        )
      )
      register_functions()
      assert list(xml.xpath('tei-aff-string(//affiliation)')) == ['Department 1, Addr Line 1']
