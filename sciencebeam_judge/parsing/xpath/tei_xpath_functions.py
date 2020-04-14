import logging
from typing import List

from lxml import etree
from natsort import natsorted

from sciencebeam_utils.utils.xml import get_text_content


LOGGER = logging.getLogger(__name__)


def _pers_name_node(node):
    if node.tag != 'persName':
        return node.find('persName')
    return node


def _filter_truthy(iterable):
    return [x for x in iterable if x]


def _filter_not_none(iterable):
    return [x for x in iterable if x is not None]


def _text(nodes: List[etree.Element]) -> List[str]:
    return _filter_truthy(
        get_text_content(x) for x in nodes
    )


def _pers_name_given_name(pers_name_node):
    return ' '.join(_text(_filter_not_none(pers_name_node.findall('forename'))))


def _pers_name_full_name(pers_name_node):
    return ' '.join(_text(_filter_not_none(
        list(pers_name_node.findall('forename')) +
        [pers_name_node.find('surname')]
    )))


def _author_given_name(author_node):
    name_node = _pers_name_node(author_node)
    if name_node is not None:
        return _pers_name_given_name(name_node)
    return None


def _author_full_name(author_node):
    name_node = _pers_name_node(author_node)
    if name_node is not None:
        return _pers_name_full_name(name_node)
    return None


def fn_tei_given_name(_, nodes):
    result = _filter_not_none([
        _author_given_name(node)
        for node in nodes
    ])
    LOGGER.debug('fn_tei_given_name, nodes: %s, result: %s', nodes, result)
    return result


def fn_tei_full_name(_, nodes):
    result = _filter_not_none([
        _author_full_name(node)
        for node in nodes
    ])
    LOGGER.debug('fn_tei_full_name, nodes: %s, result: %s', nodes, result)
    return result


def fn_tei_authors(_, nodes):
    return [
        author
        for node in nodes
        for author in node.xpath(
            'teiHeader/fileDesc/sourceDesc/biblStruct/analytic/author'
        )
    ]


def fn_tei_deduplicate_by_attrib(
        _, nodes: List[etree.Element], attrib_name: str) -> List[etree.Element]:
    seen_keys = set()
    result = []
    for node in nodes:
        key = node.attrib.get(attrib_name)
        if key and key in seen_keys:
            continue
        result.append(node)
        seen_keys.add(key)
    return result


def _sort_by_attrib(
        _, nodes: List[etree.Element], attrib_name: str) -> List[etree.Element]:
    LOGGER.debug(
        '_sort_by_attrib, nodes[@%s]=%s',
        attrib_name,
        [node.attrib.get(attrib_name) for node in nodes]
    )
    result = natsorted(nodes, key=lambda node: node.attrib.get(attrib_name, ''))
    LOGGER.debug(
        '_sort_by_attrib, result[@%s]=%s',
        attrib_name,
        [node.attrib.get(attrib_name) for node in result]
    )
    return result


def _sort_author_affiliations(nodes: List[etree.Element]):
    return _sort_by_attrib(None, nodes, attrib_name='key')


def fn_tei_author_affiliations(_, nodes):
    # xpath works with "node sets", the order is usually the document order
    # sorting here won't have any effect
    return fn_tei_deduplicate_by_attrib(
        _, [
            affiliation
            for author in fn_tei_authors(_, nodes)
            for affiliation in author.findall('affiliation')
        ],
        attrib_name='key'
    )


def _aff_string(aff):
    raw_affiliation_nodes = aff.xpath('./note[@type="raw_affiliation"]')
    if raw_affiliation_nodes:
        return ', '.join(_text(raw_affiliation_nodes))
    return ', '.join(
        _text(
            aff.findall('orgName') +
            aff.findall('address/addrLine') +
            aff.findall('address/postCode') +
            aff.findall('address/settlement') +
            aff.findall('address/country')
        )
    )


def _aff_text(aff: etree.Element):
    raw_affiliation_nodes = aff.xpath('./note[@type="raw_affiliation"]')
    return ', '.join(_text(raw_affiliation_nodes))


def fn_tei_aff_string(_, nodes):
    return [_aff_string(node) for node in _sort_author_affiliations(nodes)]


def fn_tei_aff_text(_, nodes: List[etree.Element]):
    return [_aff_text(node) for node in _sort_author_affiliations(nodes)]


def _ref_fpage(ref):
    for node in ref.xpath('.//biblScope[@unit="page"]/@from'):
        return node
    for node in ref.xpath('.//biblScope[@unit="page"]'):
        return node.text or ''
    return ''


def fn_tei_ref_fpage(_, nodes):
    return [_ref_fpage(node) for node in nodes]


def _ref_lpage(ref):
    for node in ref.xpath('.//biblScope[@unit="page"]/@to'):
        return node
    return _ref_fpage(ref)


def fn_tei_ref_lpage(_, nodes):
    return [_ref_lpage(node) for node in nodes]


def _ref_publication_type(ref):
    for _ in ref.xpath('.//title[@level="j"]'):
        return 'journal'
    for _ in ref.xpath('.//title[@level="m"]'):
        # we are assuming "book" for now
        return 'book'
    return _ref_fpage(ref)


def fn_tei_ref_publication_type(_, nodes):
    return [_ref_publication_type(node) for node in nodes]


def _iter_abstract_text_elements(abstract):
    head_list = abstract.xpath('.//head')
    children_to_exclude = head_list[:1]
    divs = abstract.xpath('.//div')
    if not divs:
        yield get_text_content(abstract)
    for node in divs:
        for child in node.xpath('.//*'):
            if child not in children_to_exclude:
                yield get_text_content(child)


def _abstract_text(abstract):
    return ' '.join(_iter_abstract_text_elements(abstract))


def fn_tei_abstract_text(_, nodes):
    return [_abstract_text(node) for node in nodes]


def register_functions(ns=None):
    if ns is None:
        ns = etree.FunctionNamespace(None)
    ns['tei-given-name'] = fn_tei_given_name
    ns['tei-full-name'] = fn_tei_full_name
    ns['tei-authors'] = fn_tei_authors
    ns['tei-aff-string'] = fn_tei_aff_string
    ns['tei-aff-text'] = fn_tei_aff_text
    ns['tei-author-affiliations'] = fn_tei_author_affiliations
    ns['tei-ref-fpage'] = fn_tei_ref_fpage
    ns['tei-ref-lpage'] = fn_tei_ref_lpage
    ns['tei-ref-publication-type'] = fn_tei_ref_publication_type
    ns['tei-abstract-text'] = fn_tei_abstract_text
