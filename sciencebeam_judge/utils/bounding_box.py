from typing import List, NamedTuple, Sequence


class BoundingRange(NamedTuple):
    start: float
    length: float

    def validate(self) -> 'BoundingRange':
        if self.length < 0:
            raise ValueError(f'length must not be less than zero, was: {self.length}')
        return self

    def intersection(self, other: 'BoundingRange') -> 'BoundingRange':
        intersection_start = max(self.start, other.start)
        intersection_end = min(self.start + self.length, other.start + other.length)
        return BoundingRange(
            intersection_start,
            max(0, intersection_end - intersection_start)
        )


class BoundingBox(NamedTuple):
    x: float
    y: float
    width: float
    height: float

    def __bool__(self):
        return not self.is_empty()

    def is_empty(self) -> bool:
        return not self.width or not self.height

    @property
    def area(self) -> float:
        return self.width * self.height

    @property
    def x_range(self):
        return BoundingRange(self.x, self.width).validate()

    @property
    def y_range(self):
        return BoundingRange(self.y, self.height).validate()

    def round(self) -> 'BoundingBox':
        return BoundingBox(round(self.x), round(self.y), round(self.width), round(self.height))

    def scale_by(self, rx: float, ry: float) -> 'BoundingBox':
        return BoundingBox(
            x=self.x * rx,
            y=self.y * ry,
            width=self.width * rx,
            height=self.height * ry
        )

    def intersection(self, other: 'BoundingBox') -> 'BoundingBox':
        intersection_x_range = self.x_range.intersection(other.x_range)
        intersection_y_range = self.y_range.intersection(other.y_range)
        return BoundingBox(
            intersection_x_range.start,
            intersection_y_range.start,
            intersection_x_range.length,
            intersection_y_range.length
        )


EMPTY_BOUNDING_BOX = BoundingBox(x=0, y=0, width=0, height=0)


class PageBoundingBox(NamedTuple):
    page_number: int
    bounding_box: BoundingBox

    def __bool__(self):
        return not self.is_empty()

    def is_empty(self) -> bool:
        return self.bounding_box.is_empty()

    @property
    def area(self) -> float:
        return self.bounding_box.area

    def round(self) -> 'PageBoundingBox':
        return PageBoundingBox(
            page_number=self.page_number,
            bounding_box=self.bounding_box.round()
        )

    def scale_by(self, rx: float, ry: float) -> 'PageBoundingBox':
        return PageBoundingBox(
            page_number=self.page_number,
            bounding_box=self.bounding_box.scale_by(rx, ry)
        )

    def intersection(self, other: 'PageBoundingBox') -> 'PageBoundingBox':
        if other.page_number != self.page_number:
            return EMPTY_PAGE_BOUNDING_BOX
        return PageBoundingBox(
            page_number=self.page_number,
            bounding_box=self.bounding_box.intersection(
                other.bounding_box
            )
        )


EMPTY_PAGE_BOUNDING_BOX = PageBoundingBox(
    page_number=0,
    bounding_box=EMPTY_BOUNDING_BOX
)


class PageBoundingBoxList(NamedTuple):
    page_bounding_box_list: Sequence[PageBoundingBox]

    def __len__(self) -> int:
        return len(self.page_bounding_box_list)

    def __bool__(self):
        return not self.is_empty()

    def is_empty(self) -> bool:
        return not self.non_empty_page_bounding_box_list

    @property
    def non_empty_page_bounding_box_list(self) -> Sequence[PageBoundingBox]:
        return [
            page_bounding_box
            for page_bounding_box in self.page_bounding_box_list
            if not page_bounding_box.is_empty()
        ]

    @property
    def area(self) -> float:
        return sum(
            page_bounding_box.area
            for page_bounding_box in self.page_bounding_box_list
        )

    def round(self) -> 'PageBoundingBoxList':
        return PageBoundingBoxList([
            page_bounding_box.round()
            for page_bounding_box in self.page_bounding_box_list
        ])

    def scale_by(self, rx: float, ry: float) -> 'PageBoundingBoxList':
        return PageBoundingBoxList([
            page_bounding_box.scale_by(rx, ry)
            for page_bounding_box in self.page_bounding_box_list
        ])

    def intersection(self, other: 'PageBoundingBoxList') -> 'PageBoundingBoxList':
        non_empty_page_bounding_box_list_1 = self.non_empty_page_bounding_box_list
        non_empty_page_bounding_box_list_2 = other.non_empty_page_bounding_box_list
        if not non_empty_page_bounding_box_list_1 or not non_empty_page_bounding_box_list_2:
            return EMPTY_PAGE_BOUNDING_BOX_LIST
        intersection_page_bounding_box_list = [
            page_bounding_box_1.intersection(page_bounding_box_2)
            for page_bounding_box_1 in non_empty_page_bounding_box_list_1
            for page_bounding_box_2 in non_empty_page_bounding_box_list_2
        ]
        non_empty_intersection_page_bounding_box_list = [
            page_bounding_box
            for page_bounding_box in intersection_page_bounding_box_list
            if not page_bounding_box.is_empty()
        ]
        if not non_empty_intersection_page_bounding_box_list:
            return EMPTY_PAGE_BOUNDING_BOX_LIST
        return PageBoundingBoxList(non_empty_intersection_page_bounding_box_list)


EMPTY_PAGE_BOUNDING_BOX_LIST = PageBoundingBoxList(tuple([]))


def get_merged_page_bounding_box_lists(
    page_bounding_box_lists: Sequence[PageBoundingBoxList]
) -> PageBoundingBoxList:
    _page_bounding_box_list: List[PageBoundingBox] = []
    for page_bounding_box_list in page_bounding_box_lists:
        _page_bounding_box_list.extend(page_bounding_box_list.non_empty_page_bounding_box_list)
    return PageBoundingBoxList(_page_bounding_box_list)
