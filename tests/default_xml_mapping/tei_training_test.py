import logging

from lxml.builder import E

from .utils import parse_xml_node


# false positive not-callable for lxml.builder.E
# pylint: disable=not-callable


LOGGER = logging.getLogger(__name__)


DOI_1 = '10.12345/abc/1'
HTTPS_DOI_URL_PREFIX = 'https://doi.org/'

TEXT_1 = 'Some text 1'


class TestTeiTraining:
    class TestTeiTrainingTitle:
        def test_should_extract_title(self, default_xml_mapping):
            xml = E.tei(E.text(E.front(
                E.docTitle(E.titlePart('Title 1')),
                E.note('other')
            )))
            result = parse_xml_node(xml, xml_mapping=default_xml_mapping)
            assert result.get('title') == ['Title 1']

        def test_should_only_match_first_title(self, default_xml_mapping):
            xml = E.tei(E.text(E.front(
                E.docTitle(E.titlePart('Title 1')),
                E.docTitle(E.titlePart('Title 2')),
            )))
            result = parse_xml_node(xml, xml_mapping=default_xml_mapping)
            assert result.get('title') == ['Title 1']

    class TestTeiTrainingAbstract:
        def test_should_extract_title(self, default_xml_mapping):
            xml = E.tei(E.text(E.front(
                E.div('Abstract 1', type='abstract'),
                E.div('other')
            )))
            result = parse_xml_node(xml, xml_mapping=default_xml_mapping)
            assert result.get('abstract') == ['Abstract 1']
