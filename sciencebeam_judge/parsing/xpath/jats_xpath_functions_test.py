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

  class TestAffString(object):
    def test_should_return_institution(self):
      xml = E.article(
        E.aff(
          E('institution', {'content-type': 'orgname'}, 'Organisation 1')
        )
      )
      register_functions()
      assert list(xml.xpath('jats-aff-string(//aff)')) == ['Organisation 1']

    def test_should_join_multiple_institutions(self):
      xml = E.article(
        E.aff(
          E('institution', {'content-type': 'orgname'}, 'Organisation 1'),
          E('institution', {'content-type': 'orgdiv1'}, 'Division 1')
        )
      )
      register_functions()
      assert list(xml.xpath('jats-aff-string(//aff)')) == ['Organisation 1, Division 1']

    def test_should_join_institution_with_city_country(self):
      xml = E.article(
        E.aff(
          E('institution', {'content-type': 'orgname'}, 'Organisation 1'),
          E.city('City 1'),
          E.country('Country 1')
        )
      )
      register_functions()
      assert list(xml.xpath('jats-aff-string(//aff)')) == ['Organisation 1, City 1, Country 1']

    def test_should_join_institution_with_addr_line(self):
      xml = E.article(
        E.aff(
          E('institution', {'content-type': 'orgname'}, 'Organisation 1'),
          E('addr-line', 'Addr Line 1')
        )
      )
      register_functions()
      assert list(xml.xpath('jats-aff-string(//aff)')) == ['Organisation 1, Addr Line 1']

    def test_should_return_aff_text_without_label(self):
      xml = E.article(
        E.aff(
          'Affiliation 1'
        )
      )
      register_functions()
      assert list(xml.xpath('jats-aff-string(//aff)')) == ['Affiliation 1']

    def test_should_return_aff_text_excluding_label(self):
      xml = E.article(
        E.aff(
          E.label('1'),
          'Affiliation 1'
        )
      )
      register_functions()
      assert list(xml.xpath('jats-aff-string(//aff)')) == ['Affiliation 1']


  class TestRefFpage(object):
    def test_should_return_from_attribute_if_present(self):
      xml = E.article(E.ref(E('mixed-citation',
        E.fpage("123")
      )))
      register_functions()
      assert list(xml.xpath('jats-ref-fpage(//ref)')) == ['123']

    def test_should_return_empty_string_if_fpage_has_no_text(self):
      xml = E.article(E.ref(E('mixed-citation',
        E.fpage()
      )))
      register_functions()
      assert list(xml.xpath('jats-ref-fpage(//ref)')) == ['']

    def test_should_return_empty_string_if_there_is_no_fpage_element(self):
      xml = E.article(E.ref(E('mixed-citation',
        E.other()
      )))
      register_functions()
      assert list(xml.xpath('jats-ref-fpage(//ref)')) == ['']


  class TestRefLpage(object):
    def test_should_return_lpage_element_if_present(self):
      xml = E.article(E.ref(E('mixed-citation',
        E.lpage("123")
      )))
      register_functions()
      assert list(xml.xpath('jats-ref-lpage(//ref)')) == ['123']

    def test_should_return_fpage_if_there_is_no_lpage(self):
      xml = E.article(E.ref(E('mixed-citation',
        E.fpage("123")
      )))
      register_functions()
      assert list(xml.xpath('jats-ref-lpage(//ref)')) == ['123']

    def test_should_return_infer_full_lpage_if_lpage_is_shorter_than_lpage(self):
      xml = E.article(E.ref(E('mixed-citation',
        E.fpage("123"),
        E.lpage("45")
      )))
      register_functions()
      assert list(xml.xpath('jats-ref-lpage(//ref)')) == ['145']
