from __future__ import division

import logging
from io import BytesIO, StringIO

from .xml import (
  parse_xml_mapping,
  parse_xml
)


LOGGING = logging.getLogger(__name__)

SOME_TEXT = 'test 123'

TABLE_LABEL_1 = 'Table 1'
TABLE_CAPTION_1 = 'Table Caption 1'

TABLE_XML_1 = (
  b'''
  <table>
    <thead>
      <tr>
        <th>Column 1</th>
        <th>Column 2</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Cell 1.1</td>
        <td>Cell 1.2</td>
      </tr>
      <tr>
        <td>Cell 2.1</td>
        <td>Cell 2.2</td>
      </tr>
    </tbody>
  </table>
  '''
)

TABLE_1 = {
  'head': [['Column 1', 'Column 2']],
  'body': [
    ['Cell 1.1', 'Cell 1.2'],
    ['Cell 2.1', 'Cell 2.2']
  ]
}


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

  def test_should_parse_table(self):
    xml = (
      b'''
      <root>
        {table}
      </root>
      '''.format(
        table=TABLE_XML_1
      )
    )
    xml_mapping = {
      'root': {
        'table1': 'table'
      }
    }
    result = parse_xml(BytesIO(xml), xml_mapping)
    assert result == {
      'table1': [TABLE_1]
    }

  def test_should_parse_table_wrap(self):
    xml = (
      b'''
      <root>
        <table-wrap id="t0002" orientation="portrait">
          <label>{table_label}</label>
          <caption><title>{table_caption}</title></caption>
          {table}
        </table-wrap>
      </root>
      '''.format(
        table_label=TABLE_LABEL_1,
        table_caption=TABLE_CAPTION_1,
        table=TABLE_XML_1
      )
    )
    xml_mapping = {
      'root': {
        'table1': 'table-wrap'
      }
    }
    result = parse_xml(BytesIO(xml), xml_mapping)
    assert result == {
      'table1': [{
        'label': TABLE_LABEL_1,
        'caption': TABLE_CAPTION_1,
        'table': TABLE_1
      }]
    }
