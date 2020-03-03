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
    class TestTei(object):
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
