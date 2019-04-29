import logging

from lxml import etree

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


def _text(nodes):
    return _filter_truthy(x.text for x in nodes)


def _pers_name_full_name(pers_name_node):
    return ' '.join(_text(_filter_not_none(
        list(pers_name_node.findall('forename')) +
        [pers_name_node.find('surname')]
    )))


def _author_full_name(author_node):
    name_node = _pers_name_node(author_node)
    if name_node is not None:
        return _pers_name_full_name(name_node)
    return None


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


def _aff_string(aff):
    return ', '.join(
        _text(
            aff.findall('orgName') +
            aff.findall('address/addrLine') +
            aff.findall('address/postCode') +
            aff.findall('address/settlement') +
            aff.findall('address/country')
        )
    )


def fn_tei_aff_string(_, nodes):
    return [_aff_string(node) for node in nodes]


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
    ns['tei-full-name'] = fn_tei_full_name
    ns['tei-authors'] = fn_tei_authors
    ns['tei-aff-string'] = fn_tei_aff_string
    ns['tei-ref-fpage'] = fn_tei_ref_fpage
    ns['tei-ref-lpage'] = fn_tei_ref_lpage
    ns['tei-abstract-text'] = fn_tei_abstract_text
