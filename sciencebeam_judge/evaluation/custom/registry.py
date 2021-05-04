from sciencebeam_judge.evaluation.custom import CustomEvaluation
from sciencebeam_judge.evaluation.custom.deleted_text import (
    DeletedTextEvaluation
)


CUSTOM_EVALUATION_CLASS_BY_NAME = {
    'deleted_text': DeletedTextEvaluation
}


def get_custom_evaluation(name: str) -> CustomEvaluation:
    return CUSTOM_EVALUATION_CLASS_BY_NAME[name]()
