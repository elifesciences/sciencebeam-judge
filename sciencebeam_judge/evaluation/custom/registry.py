from typing import Optional
from sciencebeam_judge.evaluation.custom import CustomEvaluation
from sciencebeam_judge.evaluation.custom.deleted_text import (
    DeletedTextEvaluation
)
from sciencebeam_judge.evaluation.custom.bounding_box_intersection import (
    BoundingBoxIntersectionEvaluation
)


CUSTOM_EVALUATION_CLASS_BY_NAME = {
    'deleted_text': DeletedTextEvaluation,
    'bounding_box_intersection': BoundingBoxIntersectionEvaluation
}


def create_custom_evaluation(
    custom_evaluation_factory,
    config: Optional[dict] = None
) -> CustomEvaluation:
    if not config:
        return custom_evaluation_factory()
    return custom_evaluation_factory(config=config)


def get_custom_evaluation(name: str, config: Optional[dict] = None) -> CustomEvaluation:
    return create_custom_evaluation(
        CUSTOM_EVALUATION_CLASS_BY_NAME[name],
        config=config
    )
