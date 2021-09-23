import logging
from typing import List, Optional

from sciencebeam_judge.utils.distance_matching import type_checked_distance_function
from sciencebeam_judge.utils.bounding_box import (
    BoundingBox,
    PageBoundingBox,
    PageBoundingBoxList
)
from sciencebeam_judge.evaluation.match_scoring import MatchScore
from sciencebeam_judge.evaluation.scoring_methods.scoring_methods import ScoringMethod
from sciencebeam_judge.evaluation.scoring_types.scoring_types import (
    ScoringTypeNames,
    resolve_scoring_type
)
from sciencebeam_judge.evaluation.custom import CustomEvaluation


LOGGER = logging.getLogger(__name__)


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


def get_page_bounding_box_list_area_match_score(
    page_bounding_box_list_1: PageBoundingBoxList,
    page_bounding_box_list_2: PageBoundingBoxList
) -> float:
    max_area = max(page_bounding_box_list_1.area, page_bounding_box_list_2.area)
    if not max_area:
        intersection_ratio = 1.0
        LOGGER.debug(
            'max_area=%f, intersection_ratio=%f',
            max_area, intersection_ratio
        )
        return intersection_ratio
    intersection_page_bounding_box_list = page_bounding_box_list_1.intersection(
        page_bounding_box_list_2
    )
    intersection_area = intersection_page_bounding_box_list.area
    intersection_ratio = intersection_area / max_area
    LOGGER.debug(
        'intersection_area=%f, max_area=%f, intersection_ratio=%f',
        intersection_area, max_area, intersection_ratio
    )
    return intersection_ratio


def get_formatted_page_bounding_box_list_area_match_score(
    formatted_page_bounding_box_list_1: str,
    formatted_page_bounding_box_list_2: str
) -> float:
    return get_page_bounding_box_list_area_match_score(
        parse_page_bounding_box_list(formatted_page_bounding_box_list_1),
        parse_page_bounding_box_list(formatted_page_bounding_box_list_2)
    )


BOUNDING_BOX_INTERSECTION_SCORING_METHOD = ScoringMethod(
    'bounding_box_intersection',
    type_checked_distance_function(
        get_formatted_page_bounding_box_list_area_match_score,
        str
    ),
    threshold=0.8
)


DEFAULT_BOUNDING_BOX_SCORING_TYPE_NAME = ScoringTypeNames.PARIAL_ULIST


class BoundingBoxIntersectionEvaluation(CustomEvaluation):
    def __init__(self, config: Optional[dict] = None):
        super().__init__()
        self.scoring_type_name = (  # pylint: disable=consider-using-ternary
            (config and config.get('scoring_type'))
            or DEFAULT_BOUNDING_BOX_SCORING_TYPE_NAME
        )
        self.scoring_type = resolve_scoring_type(self.scoring_type_name)

    def score(
        self,
        expected: List[str],
        actual: List[str],
        include_values: bool = True
    ) -> MatchScore:
        score_dict = self.scoring_type.score(
            expected,
            actual,
            include_values=include_values,
            measures=[BOUNDING_BOX_INTERSECTION_SCORING_METHOD]
        )
        LOGGER.debug('score_dict: %r', score_dict)
        return MatchScore.from_dict(score_dict[BOUNDING_BOX_INTERSECTION_SCORING_METHOD.name])
