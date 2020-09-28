import logging
import re
from typing import List, Optional

from lxml import etree

from sciencebeam_judge.utils.xml import get_text_content, get_normalized_text_content

from sciencebeam_judge.utils.misc import normalize_person_name


LOGGER = logging.getLogger(__name__)


XLINK_NS = 'http://www.w3.org/1999/xlink'
XLINK_HREF = '{%s}href' % XLINK_NS

DOI_URL_PATTERN = r'(?:doi.org/)(10\..*)'


def _name_node(node):
    if node.tag != 'name':
        return node.find('name')
    return node


def _string_name_node(node):
    if node.tag != 'string-name':
        return node.find('string-name')
    return node


def _filter_truthy(iterable):
    return [x for x in iterable if x]


def _filter_not_none(iterable):
    return [x for x in iterable if x is not None]


def _text(nodes):
    return _filter_truthy(x.text for x in nodes)


def _name_given_name(name_node):
    return normalize_person_name(' '.join(_text(_filter_not_none(
        [name_node.find('given-names')]
    ))))


def _name_full_name(name_node):
    return normalize_person_name(' '.join(_text(_filter_not_none(
        [name_node.find('given-names'), name_node.find('surname')]
    ))))


def _contrib_given_name(contrib_node):
    name_node = _name_node(contrib_node)
    if name_node is not None:
        return _name_given_name(name_node)
    string_name_node = _string_name_node(contrib_node)
    if string_name_node is not None:
        full_name = _name_given_name(string_name_node).strip()
        if full_name:
            return full_name
    return None


def _contrib_full_name(contrib_node):
    name_node = _name_node(contrib_node)
    if name_node is not None:
        return _name_full_name(name_node)
    string_name_node = _string_name_node(contrib_node)
    if string_name_node is not None:
        full_name = _name_full_name(string_name_node).strip()
        if full_name:
            return full_name
        return string_name_node.text
    return None


def fn_jats_given_name(_, nodes):
    result = _filter_not_none([
        _contrib_given_name(node)
        for node in nodes
    ])
    LOGGER.debug('fn_jats_given_name, nodes: %s, result: %s', nodes, result)
    return result


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


def fn_jats_ref_authors(_, nodes):
    return [
        author
        for node in nodes
        for xpath in ('.//name', './/string-name')
        for author in node.xpath(xpath)
    ]


def is_blank(text: str) -> bool:
    return not text or not text.strip()


def contains_raw_text(element: etree.Element) -> bool:
    if not is_blank(element.text):
        return True
    for child in element:
        if not is_blank(child.tail):
            return True
    return False


def _aff_string(aff):
    if contains_raw_text(aff):
        return get_normalized_text_content(aff)
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


def get_doi_from_url(url: str) -> Optional[str]:
    if not url:
        return None
    m = re.search(DOI_URL_PATTERN, url)
    if not m:
        return None
    return m.group(1)


def _ref_doi(ref: etree.Element):
    for node in ref.xpath('.//pub-id[@pub-id-type="doi"]'):
        return node.text or ''
    for node in ref.xpath('.//ext-link[@ext-link-type="uri"]'):
        href = node.attrib.get(XLINK_HREF)
        LOGGER.debug('href: %r', href)
        doi = get_doi_from_url(href)
        if doi:
            return doi
    return ''


def fn_jats_ref_doi(_, nodes: List[etree.Element]) -> List[etree.Element]:
    return [_ref_doi(node) for node in nodes]


def _ref_fpage(ref):
    for node in ref.xpath('.//fpage'):
        return node.text or ''
    return ''


def fn_jats_ref_fpage(_, nodes):
    return [_ref_fpage(node) for node in nodes]


def _full_lpage(fpage, short_lpage):
    if not short_lpage or len(short_lpage) >= len(fpage):
        return short_lpage
    return fpage[:-len(short_lpage)] + short_lpage


def _ref_lpage(ref):
    fpage = _ref_fpage(ref)
    for node in ref.xpath('.//lpage'):
        return _full_lpage(fpage, node.text or '')
    return _ref_fpage(ref)


def fn_jats_ref_lpage(_, nodes):
    return [_ref_lpage(node) for node in nodes]


def register_functions(ns=None):
    if ns is None:
        ns = etree.FunctionNamespace(None)
    ns['jats-given-name'] = fn_jats_given_name
    ns['jats-full-name'] = fn_jats_full_name
    ns['jats-authors'] = fn_jats_authors
    ns['jats-ref-authors'] = fn_jats_ref_authors
    ns['jats-aff-string'] = fn_jats_aff_string
    ns['jats-ref-doi'] = fn_jats_ref_doi
    ns['jats-ref-fpage'] = fn_jats_ref_fpage
    ns['jats-ref-lpage'] = fn_jats_ref_lpage
