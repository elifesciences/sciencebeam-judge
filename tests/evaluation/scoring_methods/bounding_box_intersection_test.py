from sciencebeam_judge.evaluation.scoring_methods.bounding_box_intersection import (
    BoundingBox,
    PageBoundingBox,
    PageBoundingBoxList
)


class TestBoundingBox:
    def test_should_calculate_area(self):
        bounding_box = BoundingBox(
            x=101, y=102, width=200, height=50
        )
        assert bounding_box.area == 200 * 50

    def test_should_calculate_intersection_with_identical_bounding_box(self):
        bounding_box = BoundingBox(110, 120, 50, 60)
        assert (
            bounding_box.intersection(bounding_box) == bounding_box
        )

    def test_should_calculate_intersection_with_smaller_contained_bounding_box(self):
        assert (
            BoundingBox(100, 100, 200, 200).intersection(
                BoundingBox(110, 120, 50, 60)
            ) == BoundingBox(110, 120, 50, 60)
        )

    def test_should_calculate_intersection_with_larger_bounding_box(self):
        assert (
            BoundingBox(110, 120, 50, 60).intersection(
                BoundingBox(100, 100, 200, 200)
            ) == BoundingBox(110, 120, 50, 60)
        )

    def test_should_calculate_intersection_with_overlapping_bounding_box(self):
        assert (
            BoundingBox(110, 120, 50, 60).intersection(
                BoundingBox(120, 110, 100, 100)
            ) == BoundingBox(120, 120, 40, 60)
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
