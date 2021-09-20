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


def get_custom_evaluation(name: str) -> CustomEvaluation:
    return CUSTOM_EVALUATION_CLASS_BY_NAME[name]()
