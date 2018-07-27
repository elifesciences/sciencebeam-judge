import logging

from lxml import etree

from sciencebeam_gym.utils.xml import get_text_content


LOGGER = logging.getLogger(__name__)


CHILD_ELEMENT_PREFIX = '$'


def get_text_content_or_blank(node):
  return get_text_content(node) if node is not None else ''


def _parse_expression(expression):
  if expression.startswith(CHILD_ELEMENT_PREFIX):
    return lambda node: (
      get_text_content_or_blank(node.find(expression[len(CHILD_ELEMENT_PREFIX):]))
    )
  return lambda _: expression


def fn_generic_concat_children(_, nodes, *expressions):
  LOGGER.debug('fn_generic_concat_children, expressions=%s, nodes: %s', expressions, nodes)
  parsed_expressions = [_parse_expression(expression) for expression in expressions]
  return [
    ''.join(fn(node) for fn in parsed_expressions).strip()
    for node in nodes
  ]


def register_functions(ns=None):
  if ns is None:
    ns = etree.FunctionNamespace(None)
  ns['generic-concat-children'] = fn_generic_concat_children
