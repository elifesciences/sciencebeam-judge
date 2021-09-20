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


def format_bounding_box(bounding_box: BoundingBox) -> str:
    return f'{bounding_box.x},{bounding_box.y},{bounding_box.width},{bounding_box.height}'


def format_page_bounding_box(page_bounding_box: PageBoundingBox) -> str:
    bounding_box_text = format_bounding_box(page_bounding_box.bounding_box)
    return f'{page_bounding_box.page_number},{bounding_box_text}'


def format_page_bounding_box_list(page_bounding_box_list: PageBoundingBoxList) -> str:
    return ';'.join((
        format_page_bounding_box(page_bounding_box)
        for page_bounding_box in page_bounding_box_list.non_empty_page_bounding_box_list
    ))
