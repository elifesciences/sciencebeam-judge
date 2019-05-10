from __future__ import division

import logging
from io import BytesIO, StringIO

from lxml import etree

from .xml import (
    parse_xml_table,
    parse_xml_items,
    parse_xml_mapping,
    parse_xml
)


LOGGING = logging.getLogger(__name__)

SOME_TEXT = 'test 123'
TEXT_1 = 'Text 1'
TEXT_2 = 'Text 2'

TABLE_LABEL_1 = 'Table 1'
TABLE_CAPTION_1 = 'Table Caption 1'

TABLE_BODY_ROWS_XML_1 = (
    '''
  <tr>
    <td>Cell 1.1</td>
    <td>Cell 1.2</td>
  </tr>
  <tr>
    <td>Cell 2.1</td>
    <td>Cell 2.2</td>
  </tr>
  '''
)


TABLE_XML_1 = (
    '''
  <table>
    <thead>
      <tr>
        <th>Column 1</th>
        <th>Column 2</th>
      </tr>
    </thead>
    <tbody>
      {table_body_rows}
    </tbody>
  </table>
  '''.format(table_body_rows=TABLE_BODY_ROWS_XML_1)
)

TABLE_1 = {
    'head': [['Column 1', 'Column 2']],
    'body': [
        ['Cell 1.1', 'Cell 1.2'],
        ['Cell 2.1', 'Cell 2.2']
    ]
}


def _single_cell_table_xml(value):
    return '<table><tbody><tr><td> %s </td></tr></tbody></table>' % value


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


class TestParseXmlTableMapping(object):
    def test_should_parse_table(self):
        result = parse_xml_table(etree.fromstring(TABLE_XML_1))
        assert result == TABLE_1

    def test_should_parse_table_without_tbody(self):
        xml = '<table>{table_body_rows}</table>'.format(
            table_body_rows=TABLE_BODY_ROWS_XML_1
        )
        result = parse_xml_table(etree.fromstring(xml))
        assert result == {
            'head': [],
            'body': TABLE_1['body']
        }

    def test_should_strip_space_around_cells(self):
        xml = _single_cell_table_xml(' %s ' % SOME_TEXT)
        result = parse_xml_table(etree.fromstring(xml))
        assert result['body'][0][0] == SOME_TEXT

    def test_should_parse_table_cell_without_text(self):
        xml = b'<table><tbody><tr><td/></tr></tbody></table>'
        result = parse_xml_table(etree.fromstring(xml))
        assert result == {
            'head': [],
            'body': [['']]
        }

    def test_should_parse_table_with_tei_row_cell(self):
        xml = '<table><row><cell>%s</cell></row></table>' % SOME_TEXT
        result = parse_xml_table(etree.fromstring(xml))
        assert result == {
            'head': [],
            'body': [[SOME_TEXT]]
        }


class TestParseXmlItems(object):
    def test_should_parse_items(self):
        xml = '<items><item>%s</item><item>%s</item></items>' % (
            TEXT_1, TEXT_2
        )
        result = parse_xml_items(etree.fromstring(xml))
        assert result == {
            'items': [TEXT_1, TEXT_2]
        }


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

    def test_should_not_fail_with_string_result(self):
        xml = b'<root><p1>value1</p1></root>'
        xml_mapping = {
            'root': {
                'prop1': 'p1/text()'
            }
        }
        result = parse_xml(BytesIO(xml), xml_mapping)
        assert result == {
            'prop1': ['value1']
        }

    def test_should_parse_table(self):
        xml = (
            '''
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
        result = parse_xml(BytesIO(xml.encode()), xml_mapping)
        assert result == {
            'table1': [TABLE_1]
        }

    def test_should_parse_table_wrap(self):
        xml = (
            '''
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
        result = parse_xml(BytesIO(xml.encode()), xml_mapping)
        assert result == {
            'table1': [{
                'label': TABLE_LABEL_1,
                'caption': TABLE_CAPTION_1,
                'table': TABLE_1
            }]
        }
