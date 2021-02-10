
class FrontFieldNames:
    TITLE = 'title'
    ABSTRACT = 'abstract'
    KEYWORDS = 'keywords'


class AuthorFieldNames:
    FIRST_AUTHOR_SURNAME = 'first_author_surname'
    CORRESP_AUTHOR_SURNAMES = 'corresp_author_surnames'
    AUTHOR_SURNAMES = 'author_surnames'

    FIRST_AUTHOR_GIVEN_NAME = 'first_author_given_name'
    CORRESP_AUTHOR_GIVEN_NAMES = 'corresp_author_given_names'
    AUTHOR_GIVEN_NAMES = 'author_given_names'

    FIRST_AUTHOR_FULL_NAME = 'first_author_full_name'
    CORRESP_AUTHOR_FULL_NAMES = 'corresp_author_full_names'
    AUTHOR_FULL_NAMES = 'author_full_names'

    CORRESP_AUTHOR_EMAILS = 'corresp_author_emails'
    AUTHOR_EMAILS = 'author_emails'


class AffiliationFieldNames:
    AFFILIATION_TEXT = 'affiliation_text'
    AFFILIATION_STRINGS = 'affiliation_strings'
    AFFILIATION_LABEL = 'affiliation_label'
    AFFILIATION_INSTITUTION = 'affiliation_institution'
    AFFILIATION_COUNTRY = 'affiliation_country'


class BodyFieldNames:
    SECTION_TITLES = 'section_titles'
    SECTION_PARAGRAPHS = 'section_paragraphs'

    BODY_REFERENCE_CITATION_TEXT = 'body_reference_citation_text'
    BODY_ASSET_CITATION_TEXT = 'body_asset_citation_text'


class BackFieldNames:
    ACKNOWLEDGEMENT = 'acknowledgement'

    BACK_SECTION_TITLES = 'back_section_titles'
    BACK_SECTION_PARAGRAPHS = 'back_section_paragraphs'


class BodyBackSectionFieldNames:
    ALL_SECTION_TITLES = 'all_section_titles'
    ALL_SECTION_PARAGRAPHS = 'all_section_paragraphs'


class TableFieldNames:
    TABLES = 'tables'
    TABLE_STRINGS = 'table_strings'
    TABLE_LABELS = 'table_labels'
    TABLE_CAPTIONS = 'table_captions'
    TABLE_LABEL_CAPTIONS = 'table_label_captions'


class FigureFieldNames:
    FIGURE_LABELS = 'figure_labels'
    FIGURE_CAPTIONS = 'figure_captions'
    FIGURE_LABEL_CAPTIONS = 'figure_label_captions'


class ReferenceFieldNames:
    FIRST_REFERENCE_TEXT = 'first_reference_text'
    FIRST_REFERENCE_FIELDS = 'first_reference_fields'
    FIRST_REFERENCE_AUTHOR_SURNAMES = 'first_reference_author_surnames'
    FIRST_REFERENCE_AUTHOR_GIVEN_NAMES = 'first_reference_author_given_names'
    FIRST_REFERENCE_AUTHOR_FULL_NAMES = 'first_reference_author_full_names'
    FIRST_REFERENCE_TITLE = 'first_reference_title'
    FIRST_REFERENCE_YEAR = 'first_reference_year'
    FIRST_REFERENCE_SOURCE = 'first_reference_source'
    FIRST_REFERENCE_PUBLICATION_TYPE = 'first_reference_publication_type'
    FIRST_REFERENCE_VOLUME = 'first_reference_volume'
    FIRST_REFERENCE_FPAGE = 'first_reference_fpage'
    FIRST_REFERENCE_LPAGE = 'first_reference_lpage'
    FIRST_REFERENCE_DOI = 'first_reference_doi'
    FIRST_REFERENCE_PMID = 'first_reference_pmid'
    FIRST_REFERENCE_PMCID = 'first_reference_pmcid'
    REFERENCE_TEXT = 'reference_text'
    REFERENCE_FIELDS = 'reference_fields'
    REFERENCE_AUTHOR_SURNAMES = 'reference_author_surnames'
    REFERENCE_AUTHOR_GIVEN_NAMES = 'reference_author_given_names'
    REFERENCE_AUTHOR_FULL_NAMES = 'reference_author_full_names'
    REFERENCE_TITLE = 'reference_title'
    REFERENCE_YEAR = 'reference_year'
    REFERENCE_SOURCE = 'reference_source'
    REFERENCE_PUBLICATION_TYPE = 'reference_publication_type'
    REFERENCE_VOLUME = 'reference_volume'
    REFERENCE_FPAGE = 'reference_fpage'
    REFERENCE_LPAGE = 'reference_lpage'
    REFERENCE_DOI = 'reference_doi'
    REFERENCE_PMID = 'reference_pmid'
    REFERENCE_PMCID = 'reference_pmcid'


def get_class_field_name_values(c: type):
    return [value for key, value in vars(c).items() if key.isupper()]


DEFAULT_AUTHOR_FIELDS = get_class_field_name_values(AuthorFieldNames)
DEFAULT_AFFILIATION_FIELDS = get_class_field_name_values(AffiliationFieldNames)

DEFAULT_REFERENCE_FIELDS = get_class_field_name_values(ReferenceFieldNames)

DEFAULT_TABLE_FIELDS = get_class_field_name_values(TableFieldNames)

DEFAULT_FIGURE_FIELDS = get_class_field_name_values(FigureFieldNames)

DEFAULT_FRONT_FIELDS = (
    get_class_field_name_values(FrontFieldNames)
) + DEFAULT_AUTHOR_FIELDS + DEFAULT_AFFILIATION_FIELDS

DEFAULT_BODY_FIELDS = (
    get_class_field_name_values(BodyFieldNames)
    + DEFAULT_TABLE_FIELDS + DEFAULT_FIGURE_FIELDS
)

DEFAULT_BACK_FIELDS = (
    get_class_field_name_values(BackFieldNames)
    + DEFAULT_REFERENCE_FIELDS
)

DEFAULT_BODY_BACK_SECTION_FIELDS = get_class_field_name_values(BodyBackSectionFieldNames)

DEFAULT_EXCLUDED_FIELDS = {
    BodyFieldNames.SECTION_PARAGRAPHS,
    BodyBackSectionFieldNames.ALL_SECTION_PARAGRAPHS,
    ReferenceFieldNames.FIRST_REFERENCE_FIELDS,
    ReferenceFieldNames.REFERENCE_FIELDS
}

DEFAULT_EXTRACTION_FIELDS_WITHOUT_EXCLUSIONS = (
    DEFAULT_FRONT_FIELDS +
    DEFAULT_BODY_FIELDS +
    DEFAULT_BACK_FIELDS +
    DEFAULT_BODY_BACK_SECTION_FIELDS
)

DEFAULT_EXTRACTION_FIELDS = [
    field_name
    for field_name in DEFAULT_EXTRACTION_FIELDS_WITHOUT_EXCLUSIONS
    if field_name not in DEFAULT_EXCLUDED_FIELDS
]
