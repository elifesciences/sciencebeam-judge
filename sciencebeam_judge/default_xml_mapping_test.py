from lxml import etree
from lxml.builder import E


def fn_jats_full_name(_, nodes):
    print('nodes:', nodes)
    return [
        ' '.join([
            n.text
            for n in [node.find('given-names'), node.find('surname')]
            if n is not None
        ])
        for node in nodes
    ]


class TestDefaultXmlMapping(object):
    class TestAuthorNames(object):
        def test_(self):
            xml = E.article(
                E.name(
                    E('given-names', 'Tom'),
                    E('surname', 'Thomson')
                )
            )
            functionNS = etree.FunctionNamespace(None)
            functionNS['jats-full-name'] = fn_jats_full_name
            assert list(xml.xpath('jats-full-name(//name)')) == ['Tom Thomson']
