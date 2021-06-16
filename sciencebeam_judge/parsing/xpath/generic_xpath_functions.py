import logging
from typing import List, Union

from lxml import etree
from lxml.builder import E

from sciencebeam_judge.utils.xml import get_text_content, get_normalized_text_content


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


def parse_xpath_or_xpaths(xpath: str) -> List[str]:
    return xpath.split('||')


def get_xpath_results(
    node: etree.ElementBase,
    xpath_or_xpaths: Union[str, List[str]]
):
    if isinstance(xpath_or_xpaths, str):
        return node.xpath(xpath_or_xpaths)
    return [
        child
        for xpath in xpath_or_xpaths
        for child in node.xpath(xpath)
    ]


def fn_generic_join_children(
    _,
    nodes: List[etree.ElementBase],
    children_xpath: str,
    sep: str
):
    LOGGER.debug(
        'fn_generic_concat_children, children_xpath=%r, sep=%r, nodes: %r',
        children_xpath, sep, nodes
    )
    return [
        sep.join(
            get_text_content(child)
            for child in get_xpath_results(node, parse_xpath_or_xpaths(children_xpath))
        ).strip()
        for node in nodes
    ]


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


def fn_generic_normalized_text_content(_, nodes):
    LOGGER.debug('fn_generic_normalized_text_content, nodes: %s', nodes)
    return [
        get_normalized_text_content(node)
        for node in nodes
    ]


def _strip_brackets(text: str) -> str:
    if not text:
        return text
    if (
        (text.startswith('[') and text.endswith(']'))
        or (text.startswith('(') and text.endswith(')'))
        or (text.startswith('{') and text.endswith('}'))
    ):
        return text[1:-1].strip()
    return text


def fn_generic_strip_brackets(_, nodes):
    LOGGER.debug('fn_generic_strip_brackets, nodes: %s', nodes)
    return [
        _strip_brackets(get_text_content(node))
        for node in nodes
    ]


def register_functions(ns=None):
    if ns is None:
        ns = etree.FunctionNamespace(None)
    ns['generic-concat-children'] = fn_generic_concat_children
    ns['generic-join-children'] = fn_generic_join_children
    ns['generic-as-items'] = fn_generic_as_items
    ns['generic-text-content'] = fn_generic_text_content
    ns['generic-normalized-text-content'] = fn_generic_normalized_text_content
    ns['generic-strip-brackets'] = fn_generic_strip_brackets
