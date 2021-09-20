from typing import NamedTuple, Sequence


class BoundingBox(NamedTuple):
    x: float
    y: float
    width: float
    height: float


class PageBoundingBox(NamedTuple):
    page_number: int
    bounding_box: BoundingBox

    @staticmethod
    def from_string(text: str) -> 'PageBoundingBoxList':
        assert text
        fragments = text.split(',')
        assert len(fragments) == 5
        return PageBoundingBox(
            page_number=int(fragments[0]),
            bounding_box=BoundingBox(
                x=float(fragments[1]),
                y=float(fragments[2]),
                width=float(fragments[3]),
                height=float(fragments[4])
            )
        )


class PageBoundingBoxList(NamedTuple):
    page_bounding_box_list: Sequence[PageBoundingBox]

    @staticmethod
    def from_string(text: str) -> 'PageBoundingBoxList':
        if not text:
            return PageBoundingBoxList([])
        fragments = text.split(';')
        return PageBoundingBoxList([
            PageBoundingBox.from_string(fragment)
            for fragment in fragments
        ])

    def __len__(self) -> int:
        return len(self.page_bounding_box_list)
