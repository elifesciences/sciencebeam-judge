from sciencebeam_judge.utils.bounding_box import (
    BoundingBox,
    PageBoundingBox,
    PageBoundingBoxList
)
from sciencebeam_judge.evaluation.scoring_methods.bounding_box_intersection import (
    format_page_bounding_box_list,
    parse_page_bounding_box_list
)


class TestParsePageBoundingBoxList:
    def test_should_parse_empty_none(self):
        result = parse_page_bounding_box_list(None)
        assert not result.page_bounding_box_list
        assert not result

    def test_should_parse_empty_string(self):
        result = parse_page_bounding_box_list('')
        assert not result.page_bounding_box_list
        assert not result

    def test_should_parse_single_bounding_box(self):
        result = parse_page_bounding_box_list(
            '101,102.22,103.33,104.44,105.55'
        )
        assert result.page_bounding_box_list
        assert result
        assert (
            result.page_bounding_box_list[0] == PageBoundingBox(
                page_number=101,
                bounding_box=BoundingBox(
                    x=102.22, y=103.33, width=104.44, height=105.55
                )
            )
        )

    def test_should_parse_multiple_bounding_box(self):
        result = parse_page_bounding_box_list(
            '101,102.22,103.33,104.44,105.55;'
            '201,202.22,203.33,204.44,205.55'
        )
        assert result.page_bounding_box_list
        assert result
        assert (
            result.page_bounding_box_list == [
                PageBoundingBox(
                    page_number=101,
                    bounding_box=BoundingBox(
                        x=102.22, y=103.33, width=104.44, height=105.55
                    )
                ),
                PageBoundingBox(
                    page_number=201,
                    bounding_box=BoundingBox(
                        x=202.22, y=203.33, width=204.44, height=205.55
                    )
                )
            ]
        )


class TestFormatPageBoundingBoxList:
    def test_should_format_empty_page_bounding_box_list(self):
        result = format_page_bounding_box_list(PageBoundingBoxList([]))
        assert result == ''

    def test_should_format_single_page_bounding_box_list_item(self):
        result = format_page_bounding_box_list(PageBoundingBoxList([
            PageBoundingBox(
                page_number=101,
                bounding_box=BoundingBox(
                    x=102.22, y=103.33, width=104.44, height=105.55
                )
            )
        ]))
        assert result == '101,102.22,103.33,104.44,105.55'

    def test_should_format_multiple_page_bounding_box_list_items(self):
        result = format_page_bounding_box_list(PageBoundingBoxList([
            PageBoundingBox(
                page_number=101,
                bounding_box=BoundingBox(
                    x=102.22, y=103.33, width=104.44, height=105.55
                )
            ),
            PageBoundingBox(
                page_number=201,
                bounding_box=BoundingBox(
                    x=202.22, y=203.33, width=204.44, height=205.55
                )
            )
        ]))
        assert result == (
            '101,102.22,103.33,104.44,105.55;'
            '201,202.22,203.33,204.44,205.55'
        )
