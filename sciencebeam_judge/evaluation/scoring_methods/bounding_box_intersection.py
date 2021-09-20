from sciencebeam_judge.utils.bounding_box import (
    BoundingBox,
    PageBoundingBox,
    PageBoundingBoxList
)


def parse_page_bounding_box(text: str) -> PageBoundingBox:
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


def parse_page_bounding_box_list(text: str) -> PageBoundingBoxList:
    if not text:
        return PageBoundingBoxList([])
    fragments = text.split(';')
    return PageBoundingBoxList([
        parse_page_bounding_box(fragment)
        for fragment in fragments
    ])
