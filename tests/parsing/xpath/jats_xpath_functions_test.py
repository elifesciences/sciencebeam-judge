import pytest

from lxml.builder import E

from sciencebeam_judge.parsing.xpath.jats_xpath_functions import register_functions


@pytest.fixture(autouse=True)
def _register_functions():
    register_functions()


class TestJatsXpathFunctions:
    class TestAuthors:
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
            assert list(xml.xpath('jats-authors(.)')) == [contrib]

    class TestFullName:
        def test_should_return_full_name_of_single_name(self):
            xml = E.article(
                E.name(
                    E('given-names', 'Tom'),
                    E('surname', 'Thomson')
                )
            )
            assert list(xml.xpath('jats-full-name(//name)')) == ['Tom Thomson']

        def test_should_return_full_name_of_single_string_name(self):
            xml = E.article(
                E(
                    'string-name',
                    E('given-names', 'Tom'),
                    E('surname', 'Thomson')
                )
            )
            assert list(xml.xpath('jats-full-name(//string-name)')) == ['Tom Thomson']

        def test_should_return_string_name_text_if_it_does_not_contain_elements(self):
            xml = E.article(
                E(
                    'string-name',
                    'Tom Thomson'
                )
            )
            assert list(xml.xpath('jats-full-name(//string-name)')) == ['Tom Thomson']

        def test_should_return_full_name_of_single_contrib(self):
            xml = E.article(
                E.contrib(
                    E.name(
                        E('given-names', 'Tom'),
                        E('surname', 'Thomson')
                    )
                )
            )
            assert list(
                xml.xpath('jats-full-name(//contrib)')
            ) == ['Tom Thomson']

        def test_should_not_add_space_if_surname_is_missing(self):
            xml = E.article(
                E.contrib(
                    E.name(
                        E('given-names', 'Tom')
                    )
                )
            )
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
            assert list(xml.xpath('jats-full-name(//contrib)')) == ['Tom']

        def test_should_return_ignore_node_if_node_is_none(self):
            xml = E.article(
                E.contrib(
                    E.name(
                        E('given-names', 'Tom')
                    )
                )
            )
            assert list(xml.xpath('jats-full-name(//contrib[2])')) == []

        def test_should_return_ignore_node_without_name(self):
            xml = E.article(
                E.contrib(
                    E.other(
                        E('given-names', 'Tom')
                    )
                )
            )
            assert list(xml.xpath('jats-full-name(//contrib)')) == []

    class TestAffString:
        def test_should_return_institution(self):
            xml = E.article(
                E.aff(
                    E('institution', {
                        'content-type': 'orgname'
                    }, 'Organisation 1')
                )
            )
            assert list(
                xml.xpath('jats-aff-string(//aff)')
            ) == ['Organisation 1']

        def test_should_join_multiple_institutions(self):
            xml = E.article(
                E.aff(
                    E('institution', {
                        'content-type': 'orgname'
                    }, 'Organisation 1'),
                    E('institution', {'content-type': 'orgdiv1'}, 'Division 1')
                )
            )
            assert list(
                xml.xpath('jats-aff-string(//aff)')
            ) == ['Organisation 1, Division 1']

        def test_should_join_institution_with_city_country(self):
            xml = E.article(
                E.aff(
                    E('institution', {
                        'content-type': 'orgname'
                    }, 'Organisation 1'),
                    E.city('City 1'),
                    E.country('Country 1')
                )
            )
            assert list(
                xml.xpath('jats-aff-string(//aff)')
            ) == ['Organisation 1, City 1, Country 1']

        def test_should_join_institution_with_addr_line(self):
            xml = E.article(
                E.aff(
                    E('institution', {
                        'content-type': 'orgname'
                    }, 'Organisation 1'),
                    E('addr-line', 'Addr Line 1')
                )
            )
            assert list(
                xml.xpath('jats-aff-string(//aff)')
            ) == ['Organisation 1, Addr Line 1']

        def test_should_return_aff_text_without_label(self):
            xml = E.article(
                E.aff(
                    'Affiliation 1'
                )
            )
            assert list(
                xml.xpath('jats-aff-string(//aff)')
            ) == ['Affiliation 1']

        def test_should_return_aff_text_excluding_label_if_only_containing_other_tags(self):
            xml = E.article(
                E.aff(
                    E.label('1'),
                    E.other('Affiliation 1')
                )
            )
            assert list(
                xml.xpath('jats-aff-string(//aff)')
            ) == ['Affiliation 1']

        def test_should_return_raw_aff_text_if_aff_contains_non_empty_text(self):
            xml = E.article(
                E.aff(
                    E.label('1'),
                    'Affiliation 1'
                )
            )
            assert list(
                xml.xpath('jats-aff-string(//aff)')
            ) == ['1 Affiliation 1']

    class TestRefAuthors:
        def test_should_return_string_name_element(self):
            string_name = E(
                'string-name',
                E('given-names', 'Tom'),
                E('surname', 'Thomson')
            )
            xml = E.article(E.ref(
                E('mixed-citation', string_name)
            ))
            assert list(xml.xpath('jats-ref-authors(//ref)')) == [string_name]

        def test_should_return_name_element(self):
            name = E(
                'name',
                E('given-names', 'Tom'),
                E('surname', 'Thomson')
            )
            xml = E.article(E.ref(
                E('element-citation', E('person-group', name))
            ))
            assert list(xml.xpath('jats-ref-authors(//ref)')) == [name]

    class TestRefFpage:
        def test_should_return_from_attribute_if_present(self):
            xml = E.article(E.ref(
                E('mixed-citation', E.fpage("123"))
            ))
            assert list(xml.xpath('jats-ref-fpage(//ref)')) == ['123']

        def test_should_return_empty_string_if_fpage_has_no_text(self):
            xml = E.article(E.ref(
                E('mixed-citation', E.fpage())
            ))
            assert list(xml.xpath('jats-ref-fpage(//ref)')) == ['']

        def test_should_return_empty_string_if_there_is_no_fpage_element(self):
            xml = E.article(E.ref(
                E('mixed-citation', E.other())
            ))
            assert list(xml.xpath('jats-ref-fpage(//ref)')) == ['']

    class TestRefLpage:
        def test_should_return_lpage_element_if_present(self):
            xml = E.article(E.ref(
                E('mixed-citation', E.lpage("123"))
            ))
            assert list(xml.xpath('jats-ref-lpage(//ref)')) == ['123']

        def test_should_return_fpage_if_there_is_no_lpage(self):
            xml = E.article(E.ref(
                E('mixed-citation', E.fpage("123"))
            ))
            assert list(xml.xpath('jats-ref-lpage(//ref)')) == ['123']

        def test_should_return_infer_full_lpage_if_lpage_is_shorter_than_lpage(self):
            xml = E.article(E.ref(
                E('mixed-citation', E.fpage("123"), E.lpage("45"))
            ))
            assert list(xml.xpath('jats-ref-lpage(//ref)')) == ['145']
