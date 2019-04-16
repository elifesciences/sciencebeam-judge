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


def fn_jats_full_name(_, nodes):
    print('nodes:', nodes)
    return [
        ' '.join([
            n.text
            for n in [node.find('given-names'), node.find('surname')]
            if n is not None
        ])
        for node in nodes
    ]


@pytest.fixture(name='default_xml_mapping', scope='session')
def _default_xml_mapping():
    register_functions()
    return parse_xml_mapping('./xml-mapping.conf')


class TestDefaultXmlMapping(object):
    class TestAuthorNames(object):
        def test_(self):
            xml = E.article(
                E.name(
                    E('given-names', 'Tom'),
                    E('surname', 'Thomson')
                )
            )
            functionNS = etree.FunctionNamespace(None)
            functionNS['jats-full-name'] = fn_jats_full_name
            assert list(xml.xpath('jats-full-name(//name)')) == ['Tom Thomson']

    class TestTeiAbstractText(object):
        def test_should_return_without_paragraph(self, default_xml_mapping):
            xml = E.TEI(E.teiHeader(E.profileDesc(E.abstract(
                'abstract1'
            ))))
            result = parse_xml(BytesIO(etree.tostring(xml)), xml_mapping=default_xml_mapping)
            LOGGER.debug('result: %s', result)
            assert result.get('abstract') == ['abstract1']

        def test_should_return_with_div_and_paragraph(self, default_xml_mapping):
            xml = E.TEI(E.teiHeader(E.profileDesc(E.abstract(E.div(
                E.p('abstract1')
            )))))
            result = parse_xml(BytesIO(etree.tostring(xml)), xml_mapping=default_xml_mapping)
            LOGGER.debug('result: %s', result)
            assert result.get('abstract') == ['abstract1']

        def test_should_ignore_first_head(self, default_xml_mapping):
            xml = E.TEI(E.teiHeader(E.profileDesc(E.abstract(E.div(
                E.head('Abstract'),
                E.p('abstract1')
            )))))
            result = parse_xml(BytesIO(etree.tostring(xml)), xml_mapping=default_xml_mapping)
            LOGGER.debug('result: %s', result)
            assert result.get('abstract') == ['abstract1']

        def test_not_should_ignore_further_head_elements(self, default_xml_mapping):
            xml = E.TEI(E.teiHeader(E.profileDesc(E.abstract(
                E.div(E.head('Abstract')),
                E.div(E.head('Sub:'), E.p('abstract1'))
            ))))
            result = parse_xml(BytesIO(etree.tostring(xml)), xml_mapping=default_xml_mapping)
            LOGGER.debug('result: %s', result)
            assert result.get('abstract') == ['Sub: abstract1']
