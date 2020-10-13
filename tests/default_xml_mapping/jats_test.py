import logging

from lxml.builder import E


from sciencebeam_judge.parsing.xpath.jats_xpath_functions import (
    XLINK_HREF
)

from .utils import parse_xml_node

# false positive not-callable for lxml.builder.E
# pylint: disable=not-callable


LOGGER = logging.getLogger(__name__)


DOI_1 = '10.12345/abc/1'
HTTPS_DOI_URL_PREFIX = 'https://doi.org/'

TEXT_1 = 'Some text 1'


class TestJats:
    class TestJatsAuthorAffiliation:
        def test_should_parse_single_affiliation(
                self, default_xml_mapping):
            xml = E.article(E.front(E('article-meta', E('contrib-group', E.aff(
                E.label('a'),
                E.institution('Institution 1'),
                ', City 1, ',
                E.country('Country 1')
            )))))
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

    class TestJatsReferenceText:
        def test_should_get_reference_text(self, default_xml_mapping):
            xml = E.article(E.back(E(
                'ref-list',
                E.ref('reference 1'),
                E.ref('reference 2')
            )))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'first_reference_text',
                    'reference_text'
                ]
            )
            assert result.get('first_reference_text') == [
                'reference 1'
            ]
            assert result.get('reference_text') == [
                'reference 1',
                'reference 2'
            ]

        def test_should_get_reference_text_for_multiple_ref_lists(self, default_xml_mapping):
            xml = E.article(E.back(
                E('ref-list', E.ref('reference 1')),
                E('ref-list', E.ref('reference 2'))
            ))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'first_reference_text',
                    'reference_text'
                ]
            )
            assert result.get('first_reference_text') == [
                'reference 1'
            ]
            assert result.get('reference_text') == [
                'reference 1',
                'reference 2'
            ]

    class TestJatsReferenceAuthorNames:
        def test_should_parse_mixed_style_jats(self, default_xml_mapping):
            xml = E.article(E.back(E(
                'ref-list',
                E.ref(E('mixed-citation', E(
                    'string-name',
                    E.surname('Surname1.1'),
                    E('given-names', 'GivenName1.1')
                ), E(
                    'string-name',
                    E.surname('Surname1.2'),
                    E('given-names', 'GivenName1.2')
                ))),
                E.ref(E('mixed-citation', E(
                    'string-name',
                    E.surname('Surname2.1'),
                    E('given-names', 'GivenName2.1')
                )))
            )))
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

        def test_should_parse_element_style_jats(self, default_xml_mapping):
            xml = E.article(E.back(E(
                'ref-list',
                E.ref(E('element-citation', E('person-group', E.name(
                    E.surname('Surname1.1'),
                    E('given-names', 'GivenName1.1')
                ), E.name(
                    E.surname('Surname1.2'),
                    E('given-names', 'GivenName1.2')
                )))),
                E.ref(E('element-citation', E('person-group', E.name(
                    E.surname('Surname2.1'),
                    E('given-names', 'GivenName2.1')
                ))))
            )))
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

        def test_should_normalize_author_name(self, default_xml_mapping):
            xml = E.article(E.back(E(
                'ref-list',
                E.ref(E('mixed-citation', E(
                    'string-name',
                    E.surname('Smith'),
                    E('given-names', 'A. M.')
                )))
            )))
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
                {'items': ['AM']}
            ]

    class TestJatsReferenceTitle:
        def test_should_parse_mixed_style_journal_article_title_and_source(
                self, default_xml_mapping):
            xml = E.article(E.back(E(
                'ref-list',
                E.ref(E.label('1'), E(
                    'mixed-citation',
                    E('article-title', 'Article 1'),
                    E.source('Journal 1'),
                    {'publication-type': 'journal'}
                ))
            )))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'reference_title',
                    'reference_source',
                    'reference_publication_type'
                ]
            )
            assert result.get('reference_title') == ['Article 1']
            assert result.get('reference_source') == ['Journal 1']
            assert result.get('reference_publication_type') == ['journal']

        def test_should_parse_mixed_style_book_chapter_title_and_source(
                self, default_xml_mapping):
            xml = E.article(E.back(E(
                'ref-list',
                E.ref(E.label('1'), E(
                    'mixed-citation',
                    E('chapter-title', 'Chapter 1'),
                    E.source('Book 1'),
                    {'publication-type': 'book'}
                ))
            )))
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
            xml = E.article(E.back(E(
                'ref-list',
                E.ref(E.label('1'), E(
                    'mixed-citation',
                    E('pub-id', 'doi1', {'pub-id-type': 'doi'}),
                    E('pub-id', 'pmid1', {'pub-id-type': 'pmid'}),
                    E('pub-id', 'pmcid1', {'pub-id-type': 'pmcid'})
                ))
            )))
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

        def test_should_parse_doi_from_doi_url(
                self, default_xml_mapping):
            xml = E.article(E.back(E(
                'ref-list',
                E.ref(E.label('1'), E(
                    'mixed-citation',
                    E('ext-link', 'Some link text', {
                        'ext-link-type': 'uri',
                        XLINK_HREF: HTTPS_DOI_URL_PREFIX + DOI_1
                    })
                ))
            )))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'first_reference_doi',
                    'reference_doi'
                ]
            )
            assert result.get('first_reference_doi') == [DOI_1]
            assert result.get('reference_doi') == [DOI_1]

    class TestJatsAcknowledgement:
        def test_should_parse_acknowledgement(
                self, default_xml_mapping):
            xml = E.article(E.back(E.ack(
                TEXT_1
            )))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=['acknowledgement']
            )
            assert result.get('acknowledgement') == [TEXT_1]
