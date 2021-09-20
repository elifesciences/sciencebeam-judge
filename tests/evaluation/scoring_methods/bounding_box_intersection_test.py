from sciencebeam_judge.evaluation.scoring_methods.bounding_box_intersection import (
    BoundingBox,
    PageBoundingBox,
    PageBoundingBoxList
)


class TestPageBoundingBoxList:
    def test_should_parse_empty_none(self):
        result = PageBoundingBoxList.from_string(None)
        assert not result.page_bounding_box_list
        assert not result

    def test_should_parse_empty_string(self):
        result = PageBoundingBoxList.from_string('')
        assert not result.page_bounding_box_list
        assert not result

    def test_should_parse_single_bounding_box(self):
        result = PageBoundingBoxList.from_string(
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
        result = PageBoundingBoxList.from_string(
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
