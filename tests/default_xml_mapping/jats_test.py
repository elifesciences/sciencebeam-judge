import logging

from lxml.builder import E


from sciencebeam_judge.parsing.xpath.jats_xpath_functions import (
    XLINK_HREF
)

from .utils import parse_xml_node

# false positive not-callable for lxml.builder.E
# pylint: disable=not-callable


LOGGER = logging.getLogger(__name__)


DOI_1 = '10.12345/abc/1'
HTTPS_DOI_URL_PREFIX = 'https://doi.org/'

LABEL_1 = 'Label 1'
TEXT_1 = 'Some text 1'

EMAIL_1 = 'name1@test'
EMAIL_2 = 'name2@test'


class TestJats:
    class TestJatsCorrespondingAuthor:
        def test_should_find_corresponding_author_via_corresp_attribute(
                self, default_xml_mapping):
            xml = E.article(E.front(E('article-meta', E('contrib-group', *[
                E.contrib(
                    {'contrib-type': 'author', 'corresp': 'yes'},
                    E.name(E.surname('Sur1'), E('given-names', 'First1')),
                    E.email(EMAIL_1)
                ),
                E.contrib(
                    {'contrib-type': 'author'},
                    E.name(E.surname('Sur2'), E('given-names', 'First2')),
                    E.email(EMAIL_2)
                )
            ]))))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'author_surnames',
                    'author_given_names',
                    'author_full_names',
                    'author_emails',
                    'corresp_author_surnames',
                    'corresp_author_given_names',
                    'corresp_author_full_names',
                    'corresp_author_emails'
                ]
            )
            assert result.get('author_surnames') == ['Sur1', 'Sur2']
            assert result.get('author_given_names') == ['First1', 'First2']
            assert result.get('author_full_names') == ['First1 Sur1', 'First2 Sur2']
            assert result.get('author_emails') == [EMAIL_1, EMAIL_2]
            assert result.get('corresp_author_surnames') == ['Sur1']
            assert result.get('corresp_author_given_names') == ['First1']
            assert result.get('corresp_author_full_names') == ['First1 Sur1']
            assert result.get('corresp_author_emails') == [EMAIL_1]

        def test_should_find_email_from_author_notes(
                self, default_xml_mapping):
            xml = E.article(E.front(E('article-meta', *[
                E('contrib-group', *[
                    E.contrib(
                        {'contrib-type': 'author', 'corresp': 'yes'},
                        E.xref({'ref-type': 'corresp', 'rid': 'cor1'}, '*')
                    ),
                    E.contrib(
                        {'contrib-type': 'author'},
                        E.xref({'ref-type': 'other', 'rid': 'other1'}, '*')
                    )
                ]),
                E('author-notes', *[
                    E.corresp({'id': 'cor1'}, 'Corresponding author: ', E.email(EMAIL_1)),
                    E.fn({'id': 'other1'}, 'Other author: ', E.email(EMAIL_2))
                ])
            ])))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'author_emails',
                    'corresp_author_emails'
                ]
            )
            assert result.get('author_emails') == [EMAIL_1, EMAIL_2]
            assert result.get('corresp_author_emails') == [EMAIL_1]

    class TestJatsAuthorAffiliation:
        def test_should_parse_single_affiliation(
                self, default_xml_mapping):
            xml = E.article(E.front(E('article-meta', E('contrib-group', E.aff(
                E.label('a'),
                E.institution('Institution 1'),
                ', City 1, ',
                E.country('Country 1')
            )))))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'affiliation_text',
                    'affiliation_label',
                    'affiliation_institution',
                    'affiliation_country'
                ]
            )
            assert result.get('affiliation_text') == ['a Institution 1, City 1, Country 1']
            assert result.get('affiliation_label') == ['a']
            assert result.get('affiliation_institution') == ['Institution 1']
            assert result.get('affiliation_country') == ['Country 1']

    class TestJatsReferenceText:
        def test_should_get_reference_text(self, default_xml_mapping):
            xml = E.article(E.back(E(
                'ref-list',
                E.ref('reference 1'),
                E.ref('reference 2')
            )))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'first_reference_text',
                    'reference_text'
                ]
            )
            assert result.get('first_reference_text') == [
                'reference 1'
            ]
            assert result.get('reference_text') == [
                'reference 1',
                'reference 2'
            ]

        def test_should_get_reference_text_for_multiple_ref_lists(self, default_xml_mapping):
            xml = E.article(E.back(
                E('ref-list', E.ref('reference 1')),
                E('ref-list', E.ref('reference 2'))
            ))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'first_reference_text',
                    'reference_text'
                ]
            )
            assert result.get('first_reference_text') == [
                'reference 1'
            ]
            assert result.get('reference_text') == [
                'reference 1',
                'reference 2'
            ]

    class TestJatsReferenceAuthorNames:
        def test_should_parse_mixed_style_jats(self, default_xml_mapping):
            xml = E.article(E.back(E(
                'ref-list',
                E.ref(E('mixed-citation', E(
                    'string-name',
                    E.surname('Surname1.1'),
                    E('given-names', 'GivenName1.1')
                ), E(
                    'string-name',
                    E.surname('Surname1.2'),
                    E('given-names', 'GivenName1.2')
                ))),
                E.ref(E('mixed-citation', E(
                    'string-name',
                    E.surname('Surname2.1'),
                    E('given-names', 'GivenName2.1')
                )))
            )))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'reference_author_surnames',
                    'reference_author_given_names',
                    'reference_author_full_names'
                ]
            )
            assert result.get('reference_author_surnames') == [
                {'items': ['Surname1.1', 'Surname1.2']},
                {'items': ['Surname2.1']}
            ]
            assert result.get('reference_author_given_names') == [
                {'items': ['GivenName1.1', 'GivenName1.2']},
                {'items': ['GivenName2.1']}
            ]
            assert result.get('reference_author_full_names') == [
                {'items': ['GivenName1.1 Surname1.1', 'GivenName1.2 Surname1.2']},
                {'items': ['GivenName2.1 Surname2.1']}
            ]

        def test_should_parse_element_style_jats(self, default_xml_mapping):
            xml = E.article(E.back(E(
                'ref-list',
                E.ref(E('element-citation', E('person-group', E.name(
                    E.surname('Surname1.1'),
                    E('given-names', 'GivenName1.1')
                ), E.name(
                    E.surname('Surname1.2'),
                    E('given-names', 'GivenName1.2')
                )))),
                E.ref(E('element-citation', E('person-group', E.name(
                    E.surname('Surname2.1'),
                    E('given-names', 'GivenName2.1')
                ))))
            )))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'reference_author_surnames',
                    'reference_author_given_names',
                    'reference_author_full_names'
                ]
            )
            assert result.get('reference_author_surnames') == [
                {'items': ['Surname1.1', 'Surname1.2']},
                {'items': ['Surname2.1']}
            ]
            assert result.get('reference_author_given_names') == [
                {'items': ['GivenName1.1', 'GivenName1.2']},
                {'items': ['GivenName2.1']}
            ]
            assert result.get('reference_author_full_names') == [
                {'items': ['GivenName1.1 Surname1.1', 'GivenName1.2 Surname1.2']},
                {'items': ['GivenName2.1 Surname2.1']}
            ]

        def test_should_normalize_author_name(self, default_xml_mapping):
            xml = E.article(E.back(E(
                'ref-list',
                E.ref(E('mixed-citation', E(
                    'string-name',
                    E.surname('Smith'),
                    E('given-names', 'A. M.')
                )))
            )))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'reference_author_surnames',
                    'reference_author_given_names',
                    'reference_author_full_names'
                ]
            )
            assert result.get('reference_author_surnames') == [
                {'items': ['Smith']}
            ]
            assert result.get('reference_author_full_names') == [
                {'items': ['AM Smith']}
            ]
            assert result.get('reference_author_given_names') == [
                {'items': ['AM']}
            ]

    class TestJatsReferenceTitle:
        def test_should_parse_mixed_style_journal_article_title_and_source(
                self, default_xml_mapping):
            xml = E.article(E.back(E(
                'ref-list',
                E.ref(E.label('1'), E(
                    'mixed-citation',
                    E('article-title', 'Article 1'),
                    E.source('Journal 1'),
                    {'publication-type': 'journal'}
                ))
            )))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'reference_title',
                    'reference_source',
                    'reference_publication_type'
                ]
            )
            assert result.get('reference_title') == ['Article 1']
            assert result.get('reference_source') == ['Journal 1']
            assert result.get('reference_publication_type') == ['journal']

        def test_should_parse_mixed_style_book_chapter_title_and_source(
                self, default_xml_mapping):
            xml = E.article(E.back(E(
                'ref-list',
                E.ref(E.label('1'), E(
                    'mixed-citation',
                    E('chapter-title', 'Chapter 1'),
                    E.source('Book 1'),
                    {'publication-type': 'book'}
                ))
            )))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'reference_title',
                    'reference_source',
                    'reference_publication_type'
                ]
            )
            assert result.get('reference_title') == ['Chapter 1']
            assert result.get('reference_source') == ['Book 1']
            assert result.get('reference_publication_type') == ['book']

    class TestJatsReferenceExternalIdentifiers:
        def test_should_parse_mixed_style_external_identifiers(
                self, default_xml_mapping):
            xml = E.article(E.back(E(
                'ref-list',
                E.ref(E.label('1'), E(
                    'mixed-citation',
                    E('pub-id', 'doi1', {'pub-id-type': 'doi'}),
                    E('pub-id', 'pmid1', {'pub-id-type': 'pmid'}),
                    E('pub-id', 'pmcid1', {'pub-id-type': 'pmcid'})
                ))
            )))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'first_reference_doi',
                    'reference_doi',
                    'first_reference_pmid',
                    'reference_pmid',
                    'first_reference_pmcid',
                    'reference_pmcid'
                ]
            )
            assert result.get('first_reference_doi') == ['doi1']
            assert result.get('reference_doi') == ['doi1']
            assert result.get('first_reference_pmid') == ['pmid1']
            assert result.get('reference_pmid') == ['pmid1']
            assert result.get('first_reference_pmcid') == ['pmcid1']
            assert result.get('reference_pmcid') == ['pmcid1']

        def test_should_parse_doi_from_doi_url(
                self, default_xml_mapping):
            xml = E.article(E.back(E(
                'ref-list',
                E.ref(E.label('1'), E(
                    'mixed-citation',
                    E('ext-link', 'Some link text', {
                        'ext-link-type': 'uri',
                        XLINK_HREF: HTTPS_DOI_URL_PREFIX + DOI_1
                    })
                ))
            )))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'first_reference_doi',
                    'reference_doi'
                ]
            )
            assert result.get('first_reference_doi') == [DOI_1]
            assert result.get('reference_doi') == [DOI_1]

    class TestJatsBodyAndBackSections:
        def test_should_parse_body_and_back_sections(
                self, default_xml_mapping):
            xml = E.article(
                E.body(E.sec(
                    E.title('Section Title 1'),
                    E.p('Section Paragraph 1')
                )),
                E.back(E.ack(
                    E.title('Acknowledgement Title'),
                    E.p('Acknowledgement Paragraph')
                ), E.sec(
                    E.title('Section Title 2'),
                    E.p('Section Paragraph 2')
                ))
            )
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'section_titles',
                    'section_paragraphs',
                    'back_section_titles',
                    'back_section_paragraphs'
                ]
            )
            assert result.get('section_titles') == ['Section Title 1']
            assert result.get('section_paragraphs') == ['Section Paragraph 1']
            assert result.get('back_section_titles') == ['Acknowledgement Title', 'Section Title 2']
            assert result.get('back_section_paragraphs') == [
                'Acknowledgement Paragraph', 'Section Paragraph 2'
            ]

        def test_should_join_multiple_body_paragraph_blocks_of_same_section(
                self, default_xml_mapping):
            xml = E.article(
                E.body(E.sec(
                    E.title('Section Title 1'),
                    E.p('Section Paragraph 1a'),
                    E.p('Section Paragraph 1b'),
                    E.sec(
                        E.title('Section Title 1.1'),
                        E.p('Section Paragraph 1.1a'),
                        E.p('Section Paragraph 1.1b')
                    )
                ), E.sec(
                    E.title('Section Title 2'),
                    E.p('Section Paragraph 2a'),
                    E.p('Section Paragraph 2b')
                ))
            )
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'section_titles',
                    'section_paragraphs'
                ]
            )
            assert result.get('section_titles') == [
                'Section Title 1', 'Section Title 1.1', 'Section Title 2'
            ]
            assert result.get('section_paragraphs') == [
                'Section Paragraph 1a\nSection Paragraph 1b',
                'Section Paragraph 1.1a\nSection Paragraph 1.1b',
                'Section Paragraph 2a\nSection Paragraph 2b'
            ]

        def test_should_join_multiple_back_paragraph_blocks_of_same_section(
                self, default_xml_mapping):
            xml = E.article(
                E.back(E.sec(
                    E.title('Section Title 1'),
                    E.p('Section Paragraph 1a'),
                    E.p('Section Paragraph 1b'),
                    E.sec(
                        E.title('Section Title 1.1'),
                        E.p('Section Paragraph 1.1a'),
                        E.p('Section Paragraph 1.1b')
                    )
                ), E.sec(
                    E.title('Section Title 2'),
                    E.p('Section Paragraph 2a'),
                    E.p('Section Paragraph 2b')
                ))
            )
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'back_section_titles',
                    'back_section_paragraphs'
                ]
            )
            assert result.get('back_section_titles') == [
                'Section Title 1', 'Section Title 1.1', 'Section Title 2'
            ]
            assert result.get('back_section_paragraphs') == [
                'Section Paragraph 1a\nSection Paragraph 1b',
                'Section Paragraph 1.1a\nSection Paragraph 1.1b',
                'Section Paragraph 2a\nSection Paragraph 2b'
            ]

    class TestJatsAcknowledgement:
        def test_should_parse_acknowledgement(
                self, default_xml_mapping):
            xml = E.article(E.back(E.ack(
                TEXT_1
            )))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=['acknowledgement']
            )
            assert result.get('acknowledgement') == [TEXT_1]

    class TestJatsAbstractReferenceCitation:
        def test_should_find_body_reference_citation(self, default_xml_mapping):
            xml = E.article(E.front(E('article-meta', E.abstract(
                'Reference to: [',
                E.xref({'ref-type': 'bibr', 'rid': 'ref1'}, '1'),
                ']'
            ))))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'abstract_reference_citation_text'
                ]
            )
            assert result.get('abstract_reference_citation_text') == ['1']

    class TestJatsBodyReferenceCitation:
        def test_should_find_body_reference_citation(self, default_xml_mapping):
            xml = E.article(E.body(E.sec(E.p(
                'Reference to: [',
                E.xref({'ref-type': 'bibr', 'rid': 'ref1'}, '1'),
                ']'
            ))))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'body_reference_citation_text'
                ]
            )
            assert result.get('body_reference_citation_text') == ['1']

    class TestJatsAbstractAssetCitation:
        def test_should_find_body_asset_citation(self, default_xml_mapping):
            xml = E.article(E.front(E('article-meta', E.abstract(
                'Assets:',
                E.xref({'ref-type': 'fig', 'rid': 'ref1'}, 'Figure 1'),
                E.xref({'ref-type': 'table', 'rid': 'ref1'}, 'Table 1'),
            ))))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'abstract_asset_citation_text'
                ]
            )
            assert result.get('abstract_asset_citation_text') == ['Figure 1', 'Table 1']

    class TestJatsBodyAssetCitation:
        def test_should_find_body_asset_citation(self, default_xml_mapping):
            xml = E.article(E.body(E.sec(E.p(
                'Assets:',
                E.xref({'ref-type': 'fig', 'rid': 'ref1'}, 'Figure 1'),
                E.xref({'ref-type': 'table', 'rid': 'ref1'}, 'Table 1'),
            ))))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'body_asset_citation_text'
                ]
            )
            assert result.get('body_asset_citation_text') == ['Figure 1', 'Table 1']

    class TestJatsStyles:
        def test_should_find_styles_in_abstract(
                self, default_xml_mapping):
            xml = E.article(E.front(E('article-meta', E.abstract(
                E.italic('italic1'),
                E.bold('bold1'),
                E.sub('subscript1'),
                E.sup('superscript1'),
                E.italic(E.bold(E.sub(E.sup('mixed1'))))
            ))))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=[
                    'abstract_style_italic',
                    'abstract_style_bold',
                    'abstract_style_subscript',
                    'abstract_style_superscript',
                ]
            )
            assert result.get('abstract_style_italic') == ['italic1', 'mixed1']
            assert result.get('abstract_style_bold') == ['bold1', 'mixed1']
            assert result.get('abstract_style_subscript') == ['subscript1', 'mixed1']
            assert result.get('abstract_style_superscript') == ['superscript1', 'mixed1']

    class TestJatsFigure:
        def test_should_parse_figure_label_and_description_in_body_section(
                self, default_xml_mapping):
            xml = E.article(E.body(E.fig(
                E.label(LABEL_1),
                E.caption(TEXT_1)
            )))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=['figure_labels', 'figure_captions', 'figure_label_captions']
            )
            assert result.get('figure_labels') == [LABEL_1]
            assert result.get('figure_captions') == [TEXT_1]
            assert result.get('figure_label_captions') == [f'{LABEL_1} {TEXT_1}']

        def test_should_parse_figure_label_and_description_in_nested_section(
                self, default_xml_mapping):
            xml = E.article(E.body(E.sec(E.sect(E.fig(
                E.label(LABEL_1),
                E.caption(TEXT_1)
            )))))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=['figure_labels', 'figure_captions', 'figure_label_captions']
            )
            assert result.get('figure_labels') == [LABEL_1]
            assert result.get('figure_captions') == [TEXT_1]
            assert result.get('figure_label_captions') == [f'{LABEL_1} {TEXT_1}']

    class TestJatsTable:
        def test_should_parse_table_label_and_description_in_body_section(
                self, default_xml_mapping):
            xml = E.article(E.body(E('table-wrap', *[
                E.label(LABEL_1),
                E.caption(TEXT_1)
            ])))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=['table_labels', 'table_captions', 'table_label_captions']
            )
            assert result.get('table_labels') == [LABEL_1]
            assert result.get('table_captions') == [TEXT_1]
            assert result.get('table_label_captions') == [f'{LABEL_1} {TEXT_1}']

        def test_should_parse_table_label_and_description_in_nested_section(
                self, default_xml_mapping):
            xml = E.article(E.body(E.sec(E.sect(E('table-wrap', *[
                E.label(LABEL_1),
                E.caption(TEXT_1)
            ])))))
            result = parse_xml_node(
                xml,
                xml_mapping=default_xml_mapping,
                fields=['table_labels', 'table_captions', 'table_label_captions']
            )
            assert result.get('table_labels') == [LABEL_1]
            assert result.get('table_captions') == [TEXT_1]
            assert result.get('table_label_captions') == [f'{LABEL_1} {TEXT_1}']
