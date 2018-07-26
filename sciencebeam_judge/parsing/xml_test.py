from __future__ import division

import logging
from io import BytesIO, StringIO

from .xml import (
  parse_xml_mapping,
  parse_xml
)


LOGGING = logging.getLogger(__name__)

SOME_TEXT = 'test 123'

class TestParseXmlMapping(object):
  def test_should_parse_multiple_sections(self):
    xml_mapping = u'''
[root1]
prop1 = parent1/p1
prop2 = parent1/p2

[root2]
prop1 = parent2/p1
prop2 = parent2/p2
'''.strip()
    expected_xml_mapping = {
      'root1': {
        'prop1': 'parent1/p1',
        'prop2': 'parent1/p2'
      },
      'root2': {
        'prop1': 'parent2/p1',
        'prop2': 'parent2/p2'
      }
    }
    result = parse_xml_mapping(StringIO(xml_mapping))
    assert result == expected_xml_mapping

class TestParseXml(object):
  def test_should_parse_single_value_properties(self):
    xml = b'<root><parent><p1>value1</p1><p2>value2</p2></parent></root>'
    xml_mapping = {
      'root': {
        'prop1': 'parent/p1',
        'prop2': 'parent/p2'
      }
    }
    result = parse_xml(BytesIO(xml), xml_mapping)
    assert result == {
      'prop1': ['value1'],
      'prop2': ['value2']
    }

  def test_should_parse_multi_value_properties(self):
    xml = b'<root><parent><p1>value1</p1><p1>value2</p1></parent></root>'
    xml_mapping = {
      'root': {
        'prop1': 'parent/p1'
      }
    }
    result = parse_xml(BytesIO(xml), xml_mapping)
    assert result == {
      'prop1': ['value1', 'value2']
    }
