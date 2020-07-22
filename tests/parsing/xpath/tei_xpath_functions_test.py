import logging
from lxml.builder import E

import pytest

from sciencebeam_judge.parsing.xpath.tei_xpath_functions import register_functions


LOGGER = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def _register_functions():
    register_functions()


def _tei_with_authors(*authors):
    return E.TEI(E.teiHeader(E.fileDesc(E.sourceDesc(E.biblStruct(E.analytic(
        *authors
    ))))))


class TestTeiXpathFunctions:
    class TestAuthors:
        def test_should_return_single_author_node(self):
            author = E.author(
                E.persName(
                    E.forename('Tom'),
                    E.surname('Thomson')
                )
            )
            xml = _tei_with_authors(author)
            assert list(xml.xpath('tei-authors(.)')) == [author]

    class TestGivenName:
        def test_should_return_given_name_of_single_pers_name(self):
            author = E.author(
                E.persName(
                    E.forename('Tom'),
                    E.surname('Thomson')
                )
            )
            xml = _tei_with_authors(author)
            assert list(
                xml.xpath('tei-given-name(//persName)')
            ) == ['Tom']

        def test_should_return_given_name_of_multiple_forenames(self):
            author = E.author(
                E.persName(
                    E.forename('Tom', type='first'),
                    E.forename('T', type='middle'),
                    E.surname('Thomson')
                )
            )
            xml = _tei_with_authors(author)
            assert list(
                xml.xpath('tei-given-name(//persName)')
            ) == ['Tom T']

    class TestFullName:
        def test_should_return_full_name_of_single_pers_name(self):
            author = E.author(
                E.persName(
                    E.forename('Tom'),
                    E.surname('Thomson')
                )
            )
            xml = _tei_with_authors(author)
            assert list(
                xml.xpath('tei-full-name(//persName)')
            ) == ['Tom Thomson']

        def test_should_return_full_name_of_multiple_forenames(self):
            author = E.author(
                E.persName(
                    E.forename('Tom', type='first'),
                    E.forename('T', type='middle'),
                    E.surname('Thomson')
                )
            )
            xml = _tei_with_authors(author)
            assert list(
                xml.xpath('tei-full-name(//persName)')
            ) == ['Tom T Thomson']

        def test_should_return_full_name_of_single_author(self):
            author = E.author(
                E.persName(
                    E.forename('Tom'),
                    E.surname('Thomson')
                )
            )
            xml = _tei_with_authors(author)
            assert list(
                xml.xpath('tei-full-name(//author)')
            ) == ['Tom Thomson']

        def test_should_not_add_space_if_surname_is_missing(self):
            author = E.author(
                E.persName(
                    E.forename('Tom')
                )
            )
            xml = _tei_with_authors(author)
            assert list(xml.xpath('tei-full-name(//author)')) == ['Tom']

        def test_should_not_add_space_if_surname_is_empty(self):
            author = E.author(
                E.persName(
                    E.forename('Tom'),
                    E.surname()
                )
            )
            xml = _tei_with_authors(author)
            assert list(xml.xpath('tei-full-name(//author)')) == ['Tom']

    class TestAuthorAffiliations:
        def test_should_return_single_affiliation_without_key(self):
            affiliation = E.affiliation(
                E.orgName('Department 1', type="department")
            )
            xml = _tei_with_authors(E.author(affiliation))
            assert list(xml.xpath('tei-author-affiliations(.)')) == [affiliation]

        def test_should_return_single_affiliation_with_key(self):
            affiliation = E.affiliation(key='aff1')
            xml = _tei_with_authors(E.author(affiliation))
            assert list(xml.xpath('tei-author-affiliations(.)')) == [affiliation]

        def test_should_return_deduplicate_affiliations_with_key(self):
            affiliation1 = E.affiliation(key='aff1')
            affiliation1_copy = E.affiliation(key='aff1')
            xml = _tei_with_authors(E.author(affiliation1), E.author(affiliation1_copy))
            assert list(xml.xpath('tei-author-affiliations(.)')) == [affiliation1]

    class TestAffString:
        def test_should_return_org_name(self):
            xml = E.TEI(
                E.affiliation(
                    E.orgName('Department 1', type="department")
                )
            )
            assert list(
                xml.xpath('tei-aff-string(//affiliation)')
            ) == ['Department 1']

        def test_should_join_multiple_org_names(self):
            xml = E.TEI(
                E.affiliation(
                    E.orgName('Department 1', type="department"),
                    E.orgName('Institution 1', type="institution")
                )
            )
            assert list(
                xml.xpath('tei-aff-string(//affiliation)')
            ) == ['Department 1, Institution 1']

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
            assert (
                list(xml.xpath('tei-aff-string(//affiliation)')) ==
                ['Department 1, Post Code 1, Settlement 1, Country 1']
            )

        def test_should_use_raw_affiliation_note_without_label_if_available(self):
            xml = E.TEI(
                E.affiliation(
                    E.note('raw affiliation 1', type='raw_affiliation'),
                    E.orgName('Department 1', type="department"),
                    E.address(
                        E.postCode('Post Code 1'),
                        E.settlement('Settlement 1'),
                        E.country('Country 1')
                    )
                )
            )
            assert (
                list(xml.xpath('tei-aff-string(//affiliation)')) ==
                ['raw affiliation 1']
            )

        def test_should_use_raw_affiliation_note_with_label_if_available(self):
            xml = E.TEI(
                E.affiliation(
                    E.note(
                        E.label('a'),
                        ' raw affiliation 1',
                        type='raw_affiliation'
                    ),
                    E.orgName('Department 1', type="department"),
                    E.address(
                        E.postCode('Post Code 1'),
                        E.settlement('Settlement 1'),
                        E.country('Country 1')
                    )
                )
            )
            assert (
                list(xml.xpath('tei-aff-string(//affiliation)')) ==
                ['a raw affiliation 1']
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
            assert list(
                xml.xpath('tei-aff-string(//affiliation)')
            ) == ['Department 1, Addr Line 1']

        def test_should_sort_affiliations(self):
            xml = E.TEI(
                E.affiliation(
                    E.orgName('Department 2', type="department"),
                    key='aff2'
                ),
                E.affiliation(
                    E.orgName('Department 1', type="department"),
                    key='aff1'
                )
            )
            assert list(
                xml.xpath('tei-aff-string(//affiliation)')
            ) == ['Department 1', 'Department 2']

        def test_should_sort_affiliations_natural_order(self):
            xml = E.TEI(
                E.affiliation(
                    E.orgName('Department 2', type="department"),
                    key='aff10'
                ),
                E.affiliation(
                    E.orgName('Department 1', type="department"),
                    key='aff9'
                )
            )
            assert list(
                xml.xpath('tei-aff-string(//affiliation)')
            ) == ['Department 1', 'Department 2']

    class TestAffText:
        def test_should_return_emtpy_string_if_no_raw_affiliation_note_available(self):
            xml = E.TEI(
                E.affiliation(
                    E.orgName('Department 1', type="department")
                )
            )
            assert (
                list(xml.xpath('tei-aff-text(//affiliation)')) ==
                ['']
            )

        def test_should_use_raw_affiliation_note_without_label_if_available(self):
            xml = E.TEI(
                E.affiliation(
                    E.note('raw affiliation 1', type='raw_affiliation'),
                    E.orgName('Department 1', type="department")
                )
            )
            assert (
                list(xml.xpath('tei-aff-text(//affiliation)')) ==
                ['raw affiliation 1']
            )

        def test_should_use_raw_affiliation_note_with_label_if_available(self):
            xml = E.TEI(
                E.affiliation(
                    E.note(
                        E.label('a'),
                        ' raw affiliation 1',
                        type='raw_affiliation'
                    ),
                    E.orgName('Department 1', type="department")
                )
            )
            assert (
                list(xml.xpath('tei-aff-text(//affiliation)')) ==
                ['a raw affiliation 1']
            )

        def test_should_sort_affiliations(self):
            xml = E.TEI(
                E.affiliation(
                    E.note('raw affiliation 2', type='raw_affiliation'),
                    key='aff2'
                ),
                E.affiliation(
                    E.note('raw affiliation 1', type='raw_affiliation'),
                    key='aff1'
                )
            )
            assert list(
                xml.xpath('tei-aff-string(//affiliation)')
            ) == ['raw affiliation 1', 'raw affiliation 2']

        def test_should_sort_affiliations_natural_order(self):
            xml = E.TEI(
                E.affiliation(
                    E.note('raw affiliation 2', type='raw_affiliation'),
                    key='aff10'
                ),
                E.affiliation(
                    E.note('raw affiliation 1', type='raw_affiliation'),
                    key='aff9'
                )
            )
            assert list(
                xml.xpath('tei-aff-string(//affiliation)')
            ) == ['raw affiliation 1', 'raw affiliation 2']

    class TestRefFpage:
        def test_should_return_from_attribute_if_present(self):
            xml = E.TEI(E.biblStruct(E.monogr(E.imprint(
                E.biblScope({"unit": "page", "from": "123"})
            ))))
            assert list(xml.xpath('tei-ref-fpage(//biblStruct)')) == ['123']

        def test_should_return_element_text_if_from_attribute_is_not_present(self):
            xml = E.TEI(E.biblStruct(E.monogr(E.imprint(
                E.biblScope("123", unit="page")
            ))))
            assert list(xml.xpath('tei-ref-fpage(//biblStruct)')) == ['123']

        def test_should_return_empty_string_if_from_attribute_is_not_present_and_has_no_text(self):
            xml = E.TEI(E.biblStruct(E.monogr(E.imprint(
                E.biblScope(unit="page")
            ))))
            assert list(xml.xpath('tei-ref-fpage(//biblStruct)')) == ['']

        def test_should_return_empty_string_if_there_is_no_page_element(self):
            xml = E.TEI(E.biblStruct(E.monogr(E.imprint(
                E.biblScope(unit="other")
            ))))
            assert list(xml.xpath('tei-ref-fpage(//biblStruct)')) == ['']

    class TestRefLpage:
        def test_should_return_to_attribute_if_present(self):
            xml = E.TEI(E.biblStruct(E.monogr(E.imprint(
                E.biblScope({"unit": "page", "to": "123"})
            ))))
            assert list(xml.xpath('tei-ref-lpage(//biblStruct)')) == ['123']

        def test_should_return_fpage_if_there_is_no_to_page(self):
            xml = E.TEI(E.biblStruct(E.monogr(E.imprint(
                E.biblScope("123", unit="page")
            ))))
            assert list(xml.xpath('tei-ref-lpage(//biblStruct)')) == ['123']

    class TestAbstractText:
        def test_should_return_without_paragraph(self):
            xml = E.TEI(E.teiHeader(E.profileDesc(E.abstract(
                'abstract1'
            ))))
            assert list(xml.xpath('tei-abstract-text(//abstract)')) == ['abstract1']

        def test_should_return_with_div_and_paragraph(self):
            xml = E.TEI(E.teiHeader(E.profileDesc(E.abstract(E.div(
                E.p('abstract1')
            )))))
            assert list(xml.xpath('tei-abstract-text(//abstract)')) == ['abstract1']

        def test_should_ignore_first_head(self):
            xml = E.TEI(E.teiHeader(E.profileDesc(E.abstract(E.div(
                E.head('Abstract'),
                E.p('abstract1')
            )))))
            assert list(xml.xpath('tei-abstract-text(//abstract)')) == ['abstract1']

        def test_not_should_ignore_further_head_elements(self):
            xml = E.TEI(E.teiHeader(E.profileDesc(E.abstract(
                E.div(E.head('Abstract')),
                E.div(E.head('Sub:'), E.p('abstract1'))
            ))))
            assert list(xml.xpath('tei-abstract-text(//abstract)')) == ['Sub: abstract1']
