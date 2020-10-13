import logging
from io import BytesIO

from lxml import etree

from sciencebeam_judge.parsing.xml import parse_xml as _parse_xml

LOGGER = logging.getLogger(__name__)


def parse_xml(*args, **kwargs):
    result = _parse_xml(*args, **kwargs)
    LOGGER.debug('result: %s', result)
    return result


def parse_xml_node(root: etree.Element, *args, **kwargs):
    LOGGER.debug('xml: %s', etree.tostring(root, encoding='unicode'))
    return parse_xml(BytesIO(etree.tostring(root)), *args, **kwargs)
