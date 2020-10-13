import logging

from lxml.builder import E

from .utils import parse_xml_node

# false positive not-callable for lxml.builder.E
# pylint: disable=not-callable


LOGGER = logging.getLogger(__name__)


DOI_1 = '10.12345/abc/1'
HTTPS_DOI_URL_PREFIX = 'https://doi.org/'

TEXT_1 = 'Some text 1'

EMAIL_1 = 'name1@test'
EMAIL_2 = 'name2@test'


class TestTei:
    class TestJatsCorrespondingAuthor:
        def test_should_find_corresponding_author_via_corresp_role(
                self, default_xml_mapping):
            xml = E.TEI(E.teiHeader(E.fileDesc(E.sourceDesc(E.biblStruct(E.analytic(
                E.author(
                    {'role': 'corresp'},
                    E.persName(E.forename('First1'), E.surname('Sur1')),
                    E.email(EMAIL_1)
                ),
                E.author(
                    E.persName(E.forename('First2'), E.surname('Sur2')),
                    E.email(EMAIL_2)
                )
            ))))))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'author_surnames',
                    'author_given_names',
                    'author_full_names',
                    'author_emails',
                    'corresp_author_surnames',
                    'corresp_author_given_names',
                    'corresp_author_full_names',
                    'corresp_author_emails'
                ]
            )
            assert result.get('author_surnames') == ['Sur1', 'Sur2']
            assert result.get('author_given_names') == ['First1', 'First2']
            assert result.get('author_full_names') == ['First1 Sur1', 'First2 Sur2']
            assert result.get('author_emails') == [EMAIL_1, EMAIL_2]
            assert result.get('corresp_author_surnames') == ['Sur1']
            assert result.get('corresp_author_given_names') == ['First1']
            assert result.get('corresp_author_full_names') == ['First1 Sur1']
            assert result.get('corresp_author_emails') == [EMAIL_1]

    class TestTeiAuthorAffiliation:
        def test_should_parse_single_affiliation(
                self, default_xml_mapping):
            xml = E.TEI(E.teiHeader(E.fileDesc(E.sourceDesc(E.biblStruct(E.analytic(
                E.author(E.affiliation(
                    E.note(
                        {'type': 'raw_affiliation'},
                        E.label('a'),
                        ' Institution 1, City 1, Country 1'
                    ),
                    E.orgName({'type': 'institution'}, 'Institution 1'),
                    E.address(
                        E.settlement('City 1'),
                        E.country('Country 1')
                    )
                ))
            ))))))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'affiliation_text',
                    'affiliation_label',
                    'affiliation_institution',
                    'affiliation_country'
                ]
            )
            assert result.get('affiliation_text') == ['a Institution 1, City 1, Country 1']
            assert result.get('affiliation_label') == ['a']
            assert result.get('affiliation_institution') == ['Institution 1']
            assert result.get('affiliation_country') == ['Country 1']

    class TestTeiReferenceAuthorNames:
        def test_should_parse_tei_ref_authors(self, default_xml_mapping):
            xml = E.TEI(E.text(E.back(E.div(E.listBibl(
                E.biblStruct(E.analytic(E.author(E.persName(
                    E.forename('GivenName1.1', type='first'),
                    E.surname('Surname1.1')
                )), E.author(E.persName(
                    E.forename('GivenName1.2', type='first'),
                    E.surname('Surname1.2')
                )))),
                E.biblStruct(E.analytic(E.author(E.persName(
                    E.forename('GivenName2.1'),
                    E.surname('Surname2.1')
                ))))
            )))))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'reference_author_surnames',
                    'reference_author_given_names',
                    'reference_author_full_names'
                ]
            )
            assert result.get('reference_author_surnames') == [
                {'items': ['Surname1.1', 'Surname1.2']},
                {'items': ['Surname2.1']}
            ]
            assert result.get('reference_author_given_names') == [
                {'items': ['GivenName1.1', 'GivenName1.2']},
                {'items': ['GivenName2.1']}
            ]
            assert result.get('reference_author_full_names') == [
                {'items': ['GivenName1.1 Surname1.1', 'GivenName1.2 Surname1.2']},
                {'items': ['GivenName2.1 Surname2.1']}
            ]

        def test_should_normalize_tei_ref_author_name(self, default_xml_mapping):
            xml = E.TEI(E.text(E.back(E.div(E.listBibl(
                E.biblStruct(E.analytic(E.author(E.persName(
                    E.forename('A', type='first'),
                    E.forename('M', type='middle'),
                    E.surname('Smith')
                ))))
            )))))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'reference_author_surnames',
                    'reference_author_given_names',
                    'reference_author_full_names'
                ]
            )
            assert result.get('reference_author_surnames') == [
                {'items': ['Smith']}
            ]
            assert result.get('reference_author_full_names') == [
                {'items': ['AM Smith']}
            ]
            assert result.get('reference_author_given_names') == [
                {'items': ['AM']},
            ]

    class TestTeiReferenceTitle:
        def test_should_parse_tei_journal_article_and_source(
                self, default_xml_mapping):
            xml = E.TEI(E.text(E.back(E.div(E.listBibl(
                E.biblStruct(E.analytic(
                    E.title('Article 1', level='a', type='main'),
                ), E.monogr(
                    E.title('Journal 1', level='j')
                ))
            )))))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'first_reference_title',
                    'reference_title',
                    'reference_source',
                    'reference_publication_type'
                ]
            )
            assert result.get('first_reference_title') == ['Article 1']
            assert result.get('reference_title') == ['Article 1']
            assert result.get('reference_source') == ['Journal 1']
            assert result.get('reference_publication_type') == ['journal']

        def test_should_parse_tei_book_chapter_and_source(
                self, default_xml_mapping):
            xml = E.TEI(E.text(E.back(E.div(E.listBibl(
                E.biblStruct(E.analytic(
                    E.title('Chapter 1', level='a', type='main')
                ), E.monogr(
                    E.title('Book 1', level='m')
                ))
            )))))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'reference_title',
                    'reference_source',
                    'reference_publication_type'
                ]
            )
            assert result.get('reference_title') == ['Chapter 1']
            assert result.get('reference_source') == ['Book 1']
            assert result.get('reference_publication_type') == ['book']

    class TestJatsReferenceExternalIdentifiers:
        def test_should_parse_mixed_style_external_identifiers(
                self, default_xml_mapping):
            xml = E.TEI(E.text(E.back(E.div(E.listBibl(
                E.biblStruct(E.analytic(
                    E.title('Chapter 1', level='a', type='main'),
                    E.idno('doi1', type='DOI'),
                    E.idno('pmid1', type='PMID'),
                    E.idno('pmcid1', type='PMCID')
                ), E.monogr(
                    E.title('Book 1', level='m')
                ))
            )))))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'first_reference_doi',
                    'reference_doi',
                    'first_reference_pmid',
                    'reference_pmid',
                    'first_reference_pmcid',
                    'reference_pmcid'
                ]
            )
            assert result.get('first_reference_doi') == ['doi1']
            assert result.get('reference_doi') == ['doi1']
            assert result.get('first_reference_pmid') == ['pmid1']
            assert result.get('reference_pmid') == ['pmid1']
            assert result.get('first_reference_pmcid') == ['pmcid1']
            assert result.get('reference_pmcid') == ['pmcid1']

    class TestTeiAbstractText:
        def test_should_return_without_paragraph(self, default_xml_mapping):
            xml = E.TEI(E.teiHeader(E.profileDesc(E.abstract(
                'abstract1'
            ))))
            result = parse_xml_node(xml, xml_mapping=default_xml_mapping)
            assert result.get('abstract') == ['abstract1']

        def test_should_return_with_div_and_paragraph(self, default_xml_mapping):
            xml = E.TEI(E.teiHeader(E.profileDesc(E.abstract(E.div(
                E.p('abstract1')
            )))))
            result = parse_xml_node(xml, xml_mapping=default_xml_mapping)
            assert result.get('abstract') == ['abstract1']

        def test_should_ignore_first_head(self, default_xml_mapping):
            xml = E.TEI(E.teiHeader(E.profileDesc(E.abstract(E.div(
                E.head('Abstract'),
                E.p('abstract1')
            )))))
            result = parse_xml_node(xml, xml_mapping=default_xml_mapping)
            assert result.get('abstract') == ['abstract1']

        def test_not_should_ignore_further_head_elements(self, default_xml_mapping):
            xml = E.TEI(E.teiHeader(E.profileDesc(E.abstract(
                E.div(E.head('Abstract')),
                E.div(E.head('Sub:'), E.p('abstract1'))
            ))))
            result = parse_xml_node(xml, xml_mapping=default_xml_mapping)
            assert result.get('abstract') == ['Sub: abstract1']

    class TestTeiAcknowledgement:
        def test_should_parse_acknowledgement(
                self, default_xml_mapping):
            xml = E.TEI(E.text(E.back(E.div(
                {'type': 'acknowledgement'},
                TEXT_1
            ))))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=['acknowledgement']
            )
            assert result.get('acknowledgement') == [TEXT_1]
