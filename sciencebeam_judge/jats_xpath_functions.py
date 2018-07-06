import logging

from lxml import etree

from sciencebeam_gym.utils.xml import get_text_content

LOGGER = logging.getLogger(__name__)

def _name_node(node):
  if node.tag != 'name':
    return node.find('name')
  return node

def _filter_truthy(iterable):
  return [x for x in iterable if x]

def _filter_not_none(iterable):
  return [x for x in iterable if x is not None]

def _text(nodes):
  return _filter_truthy(x.text for x in nodes)

def _name_full_name(name_node):
  return ' '.join(_text(_filter_not_none(
    [name_node.find('given-names'), name_node.find('surname')]
  )))

def _contrib_full_name(contrib_node):
  name_node = _name_node(contrib_node)
  if name_node is not None:
    return _name_full_name(name_node)
  string_name_node = contrib_node.find('string-name')
  if string_name_node is not None:
    return string_name_node.text
  return None

def fn_jats_full_name(_, nodes):
  result = _filter_not_none([
    _contrib_full_name(node)
    for node in nodes
  ])
  LOGGER.debug('fn_jats_full_name, nodes: %s, result: %s', nodes, result)
  return result

def fn_jats_authors(_, nodes):
  return [
    author
    for node in nodes
    for author in node.xpath(
      'front/article-meta/contrib-group[not(@contrib-type) or @contrib-type="author"]'
      '/contrib[not(@contrib-type) or @contrib-type="author" or @contrib-type="person"]'
    )
  ]

def _aff_string(aff):
  result = ', '.join(
    _text(
      aff.findall('institution') +
      aff.findall('addr-line') +
      aff.findall('city') +
      aff.findall('country')
    )
  )
  if not result:
    result = get_text_content(aff, exclude=aff.findall('label'))
  return result

def fn_jats_aff_string(_, nodes):
  return [_aff_string(node) for node in nodes]

def register_functions(ns=None):
  if ns is None:
    ns = etree.FunctionNamespace(None)
  ns['jats-full-name'] = fn_jats_full_name
  ns['jats-authors'] = fn_jats_authors
  ns['jats-aff-string'] = fn_jats_aff_string
