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


class PageBoundingBox(NamedTuple):
    page_number: int
    bounding_box: BoundingBox


class PageBoundingBoxList(NamedTuple):
    page_bounding_box_list: Sequence[PageBoundingBox]

    def __len__(self) -> int:
        return len(self.page_bounding_box_list)
