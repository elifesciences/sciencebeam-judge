import logging
from io import BytesIO

import pytest

from lxml import etree
from lxml.builder import E

from sciencebeam_judge.parsing.xml import (
    parse_xml,
    parse_xml_mapping
)

from sciencebeam_judge.parsing.xpath.xpath_functions import register_functions


LOGGER = logging.getLogger(__name__)


@pytest.fixture(name='default_xml_mapping', scope='session')
def _default_xml_mapping():
    register_functions()
    return parse_xml_mapping('./xml-mapping.conf')


def _parse_xml(*args, **kwargs):
    result = parse_xml(*args, **kwargs)
    LOGGER.debug('result: %s', result)
    return result


class TestDefaultXmlMapping:
    class TestJats:
        class TestJatsReferenceText:
            def test_should_get_reference_text(self, default_xml_mapping):
                xml = E.article(E.back(E(
                    'ref-list',
                    E.ref('reference 1'),
                    E.ref('reference 2')
                )))
                result = _parse_xml(
                    BytesIO(etree.tostring(xml)),
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
                result = _parse_xml(
                    BytesIO(etree.tostring(xml)),
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
                result = _parse_xml(
                    BytesIO(etree.tostring(xml)),
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
                result = _parse_xml(
                    BytesIO(etree.tostring(xml)),
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
                result = _parse_xml(
                    BytesIO(etree.tostring(xml)),
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
                result = _parse_xml(
                    BytesIO(etree.tostring(xml)),
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
                result = _parse_xml(
                    BytesIO(etree.tostring(xml)),
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
                result = _parse_xml(
                    BytesIO(etree.tostring(xml)),
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

    class TestTei:
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
                result = _parse_xml(
                    BytesIO(etree.tostring(xml)),
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
                result = _parse_xml(
                    BytesIO(etree.tostring(xml)),
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
                result = _parse_xml(
                    BytesIO(etree.tostring(xml)),
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
                result = _parse_xml(
                    BytesIO(etree.tostring(xml)),
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
                result = _parse_xml(
                    BytesIO(etree.tostring(xml)),
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
                result = _parse_xml(BytesIO(etree.tostring(xml)), xml_mapping=default_xml_mapping)
                assert result.get('abstract') == ['abstract1']

            def test_should_return_with_div_and_paragraph(self, default_xml_mapping):
                xml = E.TEI(E.teiHeader(E.profileDesc(E.abstract(E.div(
                    E.p('abstract1')
                )))))
                result = _parse_xml(BytesIO(etree.tostring(xml)), xml_mapping=default_xml_mapping)
                assert result.get('abstract') == ['abstract1']

            def test_should_ignore_first_head(self, default_xml_mapping):
                xml = E.TEI(E.teiHeader(E.profileDesc(E.abstract(E.div(
                    E.head('Abstract'),
                    E.p('abstract1')
                )))))
                result = _parse_xml(BytesIO(etree.tostring(xml)), xml_mapping=default_xml_mapping)
                assert result.get('abstract') == ['abstract1']

            def test_not_should_ignore_further_head_elements(self, default_xml_mapping):
                xml = E.TEI(E.teiHeader(E.profileDesc(E.abstract(
                    E.div(E.head('Abstract')),
                    E.div(E.head('Sub:'), E.p('abstract1'))
                ))))
                result = _parse_xml(BytesIO(etree.tostring(xml)), xml_mapping=default_xml_mapping)
                assert result.get('abstract') == ['Sub: abstract1']

    class TestTeiTraining:
        class TestTeiTrainingTitle:
            def test_should_extract_title(self, default_xml_mapping):
                xml = E.tei(E.text(E.front(
                    E.docTitle(E.titlePart('Title 1')),
                    E.note('other')
                )))
                result = _parse_xml(BytesIO(etree.tostring(xml)), xml_mapping=default_xml_mapping)
                assert result.get('title') == ['Title 1']

            def test_should_only_match_first_title(self, default_xml_mapping):
                xml = E.tei(E.text(E.front(
                    E.docTitle(E.titlePart('Title 1')),
                    E.docTitle(E.titlePart('Title 2')),
                )))
                result = _parse_xml(BytesIO(etree.tostring(xml)), xml_mapping=default_xml_mapping)
                assert result.get('title') == ['Title 1']

        class TestTeiTrainingAbstract:
            def test_should_extract_title(self, default_xml_mapping):
                xml = E.tei(E.text(E.front(
                    E.div('Abstract 1', type='abstract'),
                    E.div('other')
                )))
                result = _parse_xml(BytesIO(etree.tostring(xml)), xml_mapping=default_xml_mapping)
                assert result.get('abstract') == ['Abstract 1']
