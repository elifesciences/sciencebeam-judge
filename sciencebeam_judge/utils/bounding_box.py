from typing import NamedTuple, Sequence


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
        return not self.is_empty

    @property
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
        return not self.is_empty

    @property
    def is_empty(self) -> bool:
        return self.bounding_box.is_empty

    @property
    def area(self) -> float:
        return self.bounding_box.area

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
        return not self.is_empty

    @property
    def is_empty(self) -> bool:
        return not self.non_empty_page_bounding_box_list

    @property
    def non_empty_page_bounding_box_list(self) -> Sequence[PageBoundingBox]:
        return [
            page_bounding_box
            for page_bounding_box in self.page_bounding_box_list
            if not page_bounding_box.is_empty
        ]

    @property
    def area(self) -> float:
        return sum(
            page_bounding_box.area
            for page_bounding_box in self.page_bounding_box_list
        )
