import logging

from lxml import etree

from sciencebeam_utils.utils.xml import get_text_content

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


def _author_aff(author_node):
    for aff in author_node.xpath('aff'):
        yield aff
    for xref in author_node.xpath('xref[@ref-type = "aff"]'):
        for aff in author_node.getroottree().xpath('//aff[@id="%s"]' % xref.attrib['rid']):
            yield aff


def fn_jats_author_aff(_, author_nodes):
    return [
        aff
        for author in author_nodes
        for aff in _author_aff(author)
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
    ns['jats-full-name'] = fn_jats_full_name
    ns['jats-authors'] = fn_jats_authors
    ns['jats-author-aff'] = fn_jats_author_aff
    ns['jats-aff-string'] = fn_jats_aff_string
    ns['jats-ref-fpage'] = fn_jats_ref_fpage
    ns['jats-ref-lpage'] = fn_jats_ref_lpage
