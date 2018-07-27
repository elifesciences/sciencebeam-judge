# -*- coding: utf-8 -*-
from six import raise_from

from lxml import etree as ET

from ..utils.config import parse_config_as_dict
from ..utils.xml import get_text_content, get_text_content_and_ignore_children


IGNORE_MARKER = '_ignore_'
IGNORE_MARKER_WITH_SPACE = ' ' + IGNORE_MARKER + ' '


def parse_xml_mapping(xml_mapping_filename_or_fp):
  return parse_config_as_dict(xml_mapping_filename_or_fp)


def strip_namespace(it):
  for _, el in it:
    if '}' in el.tag:
      el.tag = el.tag.split('}', 1)[1]  # strip all namespaces
  return it


def parse_ignore_namespace(source, filename=None):
  try:
    result = strip_namespace(ET.iterparse(source, recover=True))
    if result.root is None:
      raise RuntimeError('invalid xml {}'.format(filename or source))
    return result.root
  except ET.XMLSyntaxError as e:
    raise_from(RuntimeError('failed to process {}'.format(filename or source)), e)


def get_stripped_text(node):
  return get_text_content(node).strip()


def parse_xml_table(table_node):
  parsed_table = {
    'head': [
      [get_stripped_text(cell) for cell in row.xpath('th')]
      for row in table_node.xpath('thead/tr')
    ],
    'body': [
      [get_stripped_text(cell) for cell in row.xpath('td')]
      for row in table_node.xpath('tbody/tr')
    ]
  }
  if not parsed_table['head'] and not parsed_table['body']:
    parsed_table['body'] = [
      [get_stripped_text(cell) for cell in row.xpath('td')]
      for row in table_node.xpath('tr')
    ]
    if not parsed_table['body']:
      parsed_table['body'] = [
        [get_stripped_text(cell) for cell in row.xpath('cell')]
        for row in table_node.xpath('row')
      ]
  return parsed_table


def parse_xml_table_wrap(table_wrap_node):
  return {
    'label': get_stripped_text(table_wrap_node.find('label')),
    'caption': get_stripped_text(table_wrap_node.find('caption')),
    'table': parse_xml_table(table_wrap_node.find('table'))
  }


def parse_xml_field_node(field_name, node, mapping):
  try:
    if node.tag == 'table':
      return parse_xml_table(node)
    if node.tag == 'table-wrap':
      return parse_xml_table_wrap(node)
  except AttributeError:
    pass
  return get_text_content_and_ignore_children(
    node,
    node.xpath(mapping[field_name + '.ignore']) if field_name + '.ignore' in mapping else None
  ).strip()


def parse_xml_field(field_name, root, mapping):
  return [
    parse_xml_field_node(
      field_name, node, mapping
    )
    for node in root.xpath(mapping[field_name])
  ]


def parse_xml(source, xml_mapping, fields=None, filename=None):
  root = parse_ignore_namespace(source, filename=filename)
  if not root.tag in xml_mapping:
    raise Exception("unrecognised tag: {} (available: {})".format(root.tag, xml_mapping.sections()))
  mapping = xml_mapping[root.tag]
  field_names = [
    k
    for k in mapping.keys()
    if (fields is None or k in fields) and '.ignore' not in k
  ]
  result = {
    field_name: parse_xml_field(field_name, root, mapping)
    for field_name in field_names
  }
  return result
