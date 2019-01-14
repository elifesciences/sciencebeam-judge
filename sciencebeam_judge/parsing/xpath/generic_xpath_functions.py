import logging

from lxml import etree
from lxml.builder import E

from sciencebeam_judge.utils.xml import get_text_content


LOGGER = logging.getLogger(__name__)


CHILD_ELEMENT_PREFIX = '$'


def _parse_expression(expression):
    if expression.startswith(CHILD_ELEMENT_PREFIX):
        return lambda node: (
            get_text_content(node.find(expression[len(CHILD_ELEMENT_PREFIX):]))
        )
    return lambda _: expression


def fn_generic_concat_children(_, nodes, *expressions):
    LOGGER.debug(
        'fn_generic_concat_children, expressions=%s, nodes: %s',
        expressions, nodes
    )
    parsed_expressions = [
        _parse_expression(expression)
        for expression in expressions
    ]
    return [
        ''.join(fn(node) for fn in parsed_expressions).strip()
        for node in nodes
    ]


def fn_generic_join_children(_, nodes, children_xpath, sep):
    result = [
        sep.join(
            get_text_content(child)
            for child in node.xpath(children_xpath)
        ).strip()
        for node in nodes
    ]
    LOGGER.debug(
        'fn_generic_join_children, children_xpath=%s, sep=%s, nodes=%s, result=%s',
        children_xpath, sep, nodes, result
    )
    return result


def _as_items_list(node, children_xpath):
    matched_children = list(node.xpath(children_xpath))
    matched_parents = {child.getparent() for child in matched_children}
    return [
        get_text_content(child) for child in matched_children
        if child not in matched_parents
    ]


def _wrap_items(items):
    return E.items(*[
        E.item(item) for item in items
    ])


def fn_generic_as_items(_, nodes, children_xpath):
    LOGGER.debug(
        'fn_generic_as_items, children_xpath=%s, nodes: %s',
        children_xpath, nodes
    )
    return [
        _wrap_items(_as_items_list(node, children_xpath))
        for node in nodes
    ]


def fn_generic_text_content(_, nodes):
    LOGGER.debug('fn_generic_text_content, nodes: %s', nodes)
    return [
        get_text_content(node).strip()
        for node in nodes
    ]


def register_functions(ns=None):
    if ns is None:
        ns = etree.FunctionNamespace(None)
    ns['generic-concat-children'] = fn_generic_concat_children
    ns['generic-join-children'] = fn_generic_join_children
    ns['generic-as-items'] = fn_generic_as_items
    ns['generic-text-content'] = fn_generic_text_content
