import logging
import random
from collections import OrderedDict
from itertools import islice
from timeit import timeit
from typing import List, Tuple

import lorem

from sciencebeam_judge.evaluation.scoring_methods import levenshtein_score

from sciencebeam_judge.utils.distance_matching import (
    DistanceMeasure,
    get_length_based_upper_bound_score,
    get_character_count_based_upper_bound_score,
    get_distance_matches
)


LOGGER = logging.getLogger(__name__)


DISTANCE_MEASURE_WITHOUT_APPROXIMATE = DistanceMeasure(levenshtein_score)

DISTANCE_MEASURE_WITH_LENGTH_ONLY_APPROXIMATE = DistanceMeasure(
    levenshtein_score,
    [
        get_length_based_upper_bound_score
    ]
)

DISTANCE_MEASURE_WITH_APPROXIMATE = DistanceMeasure(
    levenshtein_score,
    [
        get_length_based_upper_bound_score,
        get_character_count_based_upper_bound_score
    ]
)


NAMED_DISTANCE_MEASURES = OrderedDict([
    ('distance_measure_without_approximate', DISTANCE_MEASURE_WITHOUT_APPROXIMATE),
    ('distance_measure_with_length_approximate', DISTANCE_MEASURE_WITH_LENGTH_ONLY_APPROXIMATE),
    ('distance_measure_with_approximate', DISTANCE_MEASURE_WITH_APPROXIMATE)
])


class DistanceMatchesPerfTester:
    def __init__(
        self,
        name: str,
        distance_measure: DistanceMeasure,
        expected_list: List[str],
        actual_list: List[str]
    ):
        self.name = name
        self.distance_measure = distance_measure
        self.expected_list = expected_list
        self.actual_list = actual_list

    def run_once(self):
        return get_distance_matches(
            self.expected_list,
            self.actual_list,
            self.distance_measure
        )

    def run(self, number: int = 100):
        LOGGER.info('testing: %s', self.name)
        LOGGER.info('distance_measure: %s', self.distance_measure)
        match_results = self.run_once()
        mean_score = sum([m.score for m in match_results]) / max(1, len(match_results))
        LOGGER.info('mean_score: %s', mean_score)
        result = timeit('self.run_once()', globals={'self': self}, number=number)
        LOGGER.info('result: total=%s, mean=%s', result, result / number)
        return result


def modify_text(
    text: str,
    insertion_prob: float,
    deletion_prob: float,
    relative_max_start: float,
    relative_max_end: float
) -> str:
    result = []
    start = round(random.uniform(0.0, relative_max_start) * len(text))
    end = round(random.uniform(1.0 - relative_max_end, 1.0) * len(text))
    text = text[start:end]
    for c in text:
        if random.uniform(0.0, 1.0) < insertion_prob:
            result.append(random.choice(text))
        if random.uniform(0.0, 1.0) < deletion_prob:
            continue
        result.append(c)
    return ''.join(result)


def get_generated_expected_actual_list(
    paragraph_count: int = 20,
    actual_extra_paragraph_count: int = 3,
    actual_missing_paragraph_count: int = 3,
    count_arg: int = 1,
    sentence_word_range: Tuple[int, int] = (5, 20),
    sentence_range: Tuple[int, int] = (5, 20),
    insertion_prob: float = 0.2,
    deletion_prob: float = 0.2,
    relative_max_start: float = 0.1,
    relative_max_end: float = 0.1
):
    paragraphs = list(islice(lorem.paragraph(
        count_arg,
        word_range=sentence_word_range,
        sentence_range=sentence_range
    ), paragraph_count))
    LOGGER.info('paragraphs[0]: %s', paragraphs[0])
    LOGGER.info('paragraphs count: %d', len(paragraphs))
    expected_list = paragraphs
    actual_list = (
        paragraphs.copy()[actual_missing_paragraph_count:]
        + list(islice(lorem.paragraph(
            count_arg,
            word_range=sentence_word_range,
            sentence_range=sentence_range
        ), actual_extra_paragraph_count))
    )
    random.shuffle(actual_list)
    actual_list = [
        modify_text(
            text,
            insertion_prob=insertion_prob,
            deletion_prob=deletion_prob,
            relative_max_start=relative_max_start,
            relative_max_end=relative_max_end
        )
        for text in actual_list
    ]
    LOGGER.info('actual_list[0]: %s', actual_list[0])
    return expected_list, actual_list


def main():
    iteration_count = 3
    expected_list, actual_list = get_generated_expected_actual_list()
    for name, distance_measure in NAMED_DISTANCE_MEASURES.items():
        DistanceMatchesPerfTester(
            name=name,
            distance_measure=distance_measure,
            expected_list=expected_list,
            actual_list=actual_list
        ).run(iteration_count)


if __name__ == '__main__':
    logging.basicConfig(level='INFO')
    main()
