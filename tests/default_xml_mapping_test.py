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


class TestDefaultXmlMapping(object):
    class TestJats(object):
        class TestJatsReferenceAuthorNames(object):
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

        class TestJatsReferenceTitle(object):
            def test_should_parse_mixed_style_journal_article_title_and_source(
                    self, default_xml_mapping):
                xml = E.article(E.back(E(
                    'ref-list',
                    E.ref(E('mixed-citation', E(
                        'article-title',
                        'Article 1'
                    ), E.source('Journal 1')))
                )))
                result = _parse_xml(
                    BytesIO(etree.tostring(xml)),
                    xml_mapping=default_xml_mapping,
                    fields=[
                        'reference_title',
                        'reference_source'
                    ]
                )
                assert result.get('reference_title') == ['Article 1']
                assert result.get('reference_source') == ['Journal 1']

            def test_should_parse_mixed_style_book_chapter_title_and_source(
                    self, default_xml_mapping):
                xml = E.article(E.back(E(
                    'ref-list',
                    E.ref(E('mixed-citation', E(
                        'chapter-title',
                        'Chapter 1'
                    ), E.source('Book 1')))
                )))
                result = _parse_xml(
                    BytesIO(etree.tostring(xml)),
                    xml_mapping=default_xml_mapping,
                    fields=[
                        'reference_title',
                        'reference_source'
                    ]
                )
                assert result.get('reference_title') == ['Chapter 1']
                assert result.get('reference_source') == ['Book 1']

    class TestTei(object):
        class TestTeiReferenceAuthorNames(object):
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

        class TestTeiReferenceTitle(object):
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
                        'reference_title',
                        'reference_source'
                    ]
                )
                assert result.get('reference_title') == ['Article 1']
                assert result.get('reference_source') == ['Journal 1']

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
                        'reference_source'
                    ]
                )
                assert result.get('reference_title') == ['Chapter 1']
                assert result.get('reference_source') == ['Book 1']

        class TestTeiAbstractText(object):
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

    class TestTeiTraining(object):
        class TestTeiTrainingTitle(object):
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

        class TestTeiTrainingAbstract(object):
            def test_should_extract_title(self, default_xml_mapping):
                xml = E.tei(E.text(E.front(
                    E.div('Abstract 1', type='abstract'),
                    E.div('other')
                )))
                result = _parse_xml(BytesIO(etree.tostring(xml)), xml_mapping=default_xml_mapping)
                assert result.get('abstract') == ['Abstract 1']
