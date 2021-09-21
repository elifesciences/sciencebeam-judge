import logging

from sciencebeam_judge.utils.bounding_box import (
    BoundingBox,
    PageBoundingBox,
    PageBoundingBoxList
)


LOGGER = logging.getLogger(__name__)


class TestBoundingBox:
    def test_should_indicate_empty_for_bounding_box_with_zero_width(self):
        bounding_box = BoundingBox(
            x=101, y=102, width=0, height=50
        )
        assert bounding_box.is_empty()
        assert not bounding_box
        assert not bounding_box.area

    def test_should_indicate_empty_for_bounding_box_with_zero_height(self):
        bounding_box = BoundingBox(
            x=101, y=102, width=200, height=0
        )
        assert bounding_box.is_empty()
        assert not bounding_box
        assert not bounding_box.area

    def test_should_indicate_not_empty_for_bounding_box_with_non_zero_width_height(self):
        bounding_box = BoundingBox(
            x=101, y=102, width=200, height=50
        )
        assert not bounding_box.is_empty()
        assert bounding_box

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


class TestPageBoundingBox:
    def test_should_indicate_empty_for_empty_bounding_box(self):
        page_bounding_box = PageBoundingBox(
            page_number=1,
            bounding_box=BoundingBox(
                x=101, y=102, width=200, height=0
            )
        )
        assert page_bounding_box.is_empty()
        assert not page_bounding_box
        assert not page_bounding_box.area

    def test_should_indicate_not_empty_for_non_bounding_box(self):
        page_bounding_box = PageBoundingBox(
            page_number=1,
            bounding_box=BoundingBox(
                x=101, y=102, width=200, height=50
            )
        )
        assert not page_bounding_box.is_empty()
        assert page_bounding_box

    def test_should_calculate_intersection_with_same_page_number(self):
        result = (
            PageBoundingBox(
                page_number=1,
                bounding_box=BoundingBox(110, 120, 50, 60)
            ).intersection(
                PageBoundingBox(
                    page_number=1,
                    bounding_box=BoundingBox(120, 110, 100, 100)
                )
            )
        )
        assert result == PageBoundingBox(
            page_number=1,
            bounding_box=BoundingBox(120, 120, 40, 60)
        )

    def test_should_calculate_intersection_with_different_page_number(self):
        result = (
            PageBoundingBox(
                page_number=1,
                bounding_box=BoundingBox(110, 120, 50, 60)
            ).intersection(
                PageBoundingBox(
                    page_number=2,
                    bounding_box=BoundingBox(120, 110, 100, 100)
                )
            )
        )
        assert result.is_empty()


class TestPageBoundingBoxList:
    def test_should_indicate_empty_for_empty_list(self):
        page_bounding_box_list = PageBoundingBoxList([])
        assert page_bounding_box_list.is_empty()
        assert not page_bounding_box_list
        assert not page_bounding_box_list.area

    def test_should_indicate_empty_for_empty_bounding_box(self):
        page_bounding_box_list = PageBoundingBoxList([PageBoundingBox(
            page_number=1,
            bounding_box=BoundingBox(
                x=101, y=102, width=200, height=0
            )
        )])
        assert page_bounding_box_list.is_empty()
        assert not page_bounding_box_list
        assert not page_bounding_box_list.area

    def test_should_indicate_not_empty_for_non_bounding_box(self):
        page_bounding_box_list = PageBoundingBoxList([PageBoundingBox(
            page_number=1,
            bounding_box=BoundingBox(
                x=101, y=102, width=200, height=50
            )
        )])
        assert not page_bounding_box_list.is_empty()
        assert page_bounding_box_list

    def test_should_calculate_intersection_non_empty_with_empty_page_bounding_box_list(self):
        result = (
            PageBoundingBoxList([
                PageBoundingBox(
                    page_number=1,
                    bounding_box=BoundingBox(110, 120, 50, 60)
                )
            ]).intersection(PageBoundingBoxList([]))
        )
        assert result.is_empty()

    def test_should_calculate_intersection_empty_with_non_empty_page_bounding_box_list(self):
        result = (
            PageBoundingBoxList([]).intersection(PageBoundingBoxList([
                PageBoundingBox(
                    page_number=1,
                    bounding_box=BoundingBox(120, 110, 100, 100)
                )
            ]))
        )
        assert result.is_empty()

    def test_should_calculate_intersection_with_single_other_overlapping_page_bounding_box(self):
        result = (
            PageBoundingBoxList([
                PageBoundingBox(
                    page_number=1,
                    bounding_box=BoundingBox(110, 120, 50, 60)
                )
            ]).intersection(PageBoundingBoxList([
                PageBoundingBox(
                    page_number=1,
                    bounding_box=BoundingBox(120, 110, 100, 100)
                )
            ]))
        )
        LOGGER.debug('result: %r', result)
        assert result == PageBoundingBoxList([PageBoundingBox(
            page_number=1,
            bounding_box=BoundingBox(120, 120, 40, 60)
        )])

    def test_should_calculate_intersection_with_multiple_other_overlapping_page_bounding_box(
        self
    ):
        result = (
            PageBoundingBoxList([
                PageBoundingBox(
                    page_number=1,
                    bounding_box=BoundingBox(110, 120, 50, 60)
                ),
                PageBoundingBox(
                    page_number=2,
                    bounding_box=BoundingBox(110, 120, 50, 60)
                )
            ]).intersection(PageBoundingBoxList([
                PageBoundingBox(
                    page_number=2,
                    bounding_box=BoundingBox(120, 110, 100, 100)
                ),
                PageBoundingBox(
                    page_number=1,
                    bounding_box=BoundingBox(120, 110, 100, 100)
                )
            ]))
        )
        LOGGER.debug('result: %r', result)
        assert result == PageBoundingBoxList([
            PageBoundingBox(
                page_number=1,
                bounding_box=BoundingBox(120, 120, 40, 60)
            ),
            PageBoundingBox(
                page_number=2,
                bounding_box=BoundingBox(120, 120, 40, 60)
            )
        ])
