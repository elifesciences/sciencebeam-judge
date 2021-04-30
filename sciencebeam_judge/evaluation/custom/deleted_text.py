import logging
import re
from collections import deque
from typing import AnyStr, List, NamedTuple, Deque, Tuple

from sciencebeam_alignment.align import LocalSequenceMatcher, SimpleScoring

from sciencebeam_judge.utils.seq_matching import (
    MatchingBlocks,
    StringView,
    translate_string_view_matching_blocks
)
from sciencebeam_judge.utils.distance_matching import (
    WrappedValue,
    DistanceMatch,
    get_distance_matches
)
from sciencebeam_judge.evaluation.math import safe_mean

from sciencebeam_judge.evaluation.scoring_types.list import (
    _combine_partial_match_scores
)

from sciencebeam_judge.evaluation.custom import CustomEvaluation
from sciencebeam_judge.evaluation.match_scoring import MatchScore, get_match_score_for_score

from sciencebeam_judge.evaluation.scoring_methods import (
    ScoringMethodNames,
    SCORING_METHODS_MAP
)


LOGGER = logging.getLogger(__name__)


DEFAULT_SCORING = SimpleScoring(
    match_score=2,
    mismatch_score=-1,
    gap_score=-2
)


def combine_partial_match_scores(
    scores: List[MatchScore],
    template_score: MatchScore
):
    return MatchScore.from_dict(_combine_partial_match_scores(
        [score.to_dict() for score in scores],
        template_score.to_dict()
    ))


class TextFragment(NamedTuple):
    text: str

    def __str__(self):
        return self.text

    def __len__(self):
        return len(self.text)


class FuzzyTextFragmentMatchResult(NamedTuple):
    value_1: TextFragment
    value_2: TextFragment
    score: float


DISTANCE_MEASURE = SCORING_METHODS_MAP[ScoringMethodNames.LEVENSHTEIN].distance_measure


def iter_regex_split_with_index(text: str, sep_pattern: str) -> List[Tuple[int, str]]:
    start_index = 0
    for m in re.finditer(sep_pattern, text):
        current_index = m.start(0)
        if current_index > start_index:
            yield start_index, text[start_index:current_index]
        start_index = current_index + 1
    if start_index < len(text):
        yield start_index, text[start_index:]


def get_distance_match_sort_key(
    distance_match: DistanceMatch,
    max_sort_key: Tuple[int, int]
) -> Tuple[int, int]:
    return (
        distance_match.value_1.index if distance_match.value_1 else max_sort_key[0],
        distance_match.value_2.index if distance_match.value_2 else max_sort_key[1]
    )


def get_fuzzy_matched_characters(
    haystack_str: str,
    needles: List[str],
    threshold: float
):  # pylint: disable=too-many-locals, too-many-statements
    if not haystack_str:
        return []
    wrapped_haystack_values = [
        WrappedValue(value, index)
        for index, value in iter_regex_split_with_index(haystack_str, r'\n')
    ]
    wrapped_needles = [
        WrappedValue(value, index)
        for index, value in enumerate(needles)
    ]
    distance_matches = get_distance_matches(
        wrapped_haystack_values,
        wrapped_needles,
        distance_measure=DISTANCE_MEASURE,
        threshold=threshold
    )
    haystack_matched = [False] * len(haystack_str)
    remaining_paired_sequences: Deque[WrappedValue] = deque()
    remaining_unpaired_sequences: Deque[WrappedValue] = deque()
    # using distances matches to start with more likely pairings
    max_sort_key = (len(haystack_str), len(needles))
    distance_matches = sorted(distance_matches, key=lambda distance_match: (
        get_distance_match_sort_key(distance_match, max_sort_key)
    ))
    LOGGER.debug('distance_matches: %s (threshold=%s)', distance_matches, threshold)
    for distance_match in distance_matches:
        LOGGER.debug(
            'distance_match: %s (index: %s)',
            distance_match,
            distance_match.value_1.index if distance_match.value_1 else None
        )
        if not distance_match.value_2:
            # not interested in added text at the moment
            continue
        if not distance_match.value_1:
            remaining_unpaired_sequences.append(distance_match.value_2)
            continue
        remaining_paired_sequences.append((distance_match.value_1, distance_match.value_2))
        del distance_match
    wrapped_haystack = WrappedValue(haystack_str, 0)
    while remaining_paired_sequences or remaining_unpaired_sequences:
        if remaining_paired_sequences:
            # prioritise paired sequences, they will be faster to calculate
            value_1, value_2 = remaining_paired_sequences.popleft()
        else:
            value_1 = wrapped_haystack
            value_2 = remaining_unpaired_sequences.popleft()
        value_1_view = StringView(str(value_1), [
            not t for t in haystack_matched[value_1.index:value_1.index + len(value_1)]
        ])
        value_2_view = StringView(str(value_2), [True] * len(value_2))
        LOGGER.debug(
            'value_1: %r (index: %s), value_2: %r',
            value_1_view, value_1.index, value_2_view
        )
        if not value_1_view or not value_2_view:
            LOGGER.debug('ignoring, either value 1 or value 2 are empty')
            continue
        sm = LocalSequenceMatcher(
            str(value_1_view),
            str(value_2_view),
            DEFAULT_SCORING
        )
        mb = sm.get_matching_blocks()
        matching_blocks = MatchingBlocks(mb).non_empty
        LOGGER.debug('matching_blocks: %s', matching_blocks)
        if not matching_blocks:
            # no match
            if value_1 != wrapped_haystack:
                # try on the whole sequence again
                remaining_unpaired_sequences.append(value_2)
            continue
        match_count = sum(size for _, _, size in mb)
        match_ratio = match_count / len(value_2)
        LOGGER.debug(
            'match_count=%d, match_ratio=%s, mb=%s, needle=%r',
            match_count, match_ratio, mb, value_2
        )
        # if match_ratio < threshold:
        #     remaining_needles.append(distance_match.value_2)
        #     continue
        matching_blocks = translate_string_view_matching_blocks(
            matching_blocks,
            value_1_view,
            value_2_view
        )
        matching_blocks = matching_blocks.with_offset(value_1.index, 0)
        for ai, _, size in matching_blocks:
            haystack_matched[ai:ai + size] = [True] * size
        b_start_offset = matching_blocks.start_b
        if b_start_offset:
            remaining_text = str(value_2)[:b_start_offset].strip()
            LOGGER.debug('b_start_offset: %s (%r)', b_start_offset, remaining_text)
            remaining_unpaired_sequences.append(remaining_text)
        b_end_offset = matching_blocks.end_b
        if b_end_offset < len(value_2):
            remaining_text = str(value_2)[b_end_offset:].strip()
            LOGGER.debug('b_end_offset: %s (%r)', b_end_offset, remaining_text)
            remaining_unpaired_sequences.append(remaining_text)
    return haystack_matched


def get_fuzzy_matched_text_fragments(
    expected: List[str],
    actual: List[str]
) -> List[FuzzyTextFragmentMatchResult]:
    haystack_str = '\n'.join(expected)
    needles = actual
    threshold = 0.7
    if not haystack_str:
        return []
    haystack_matched = get_fuzzy_matched_characters(
        haystack_str=haystack_str,
        needles=needles,
        threshold=threshold
    )
    match_start_index = 0
    mismatch_start_index = 0
    result = []
    for index, is_match in enumerate(haystack_matched):
        if is_match:
            if mismatch_start_index < index:
                text_fragment = TextFragment(text=haystack_str[mismatch_start_index:index])
                result.append(FuzzyTextFragmentMatchResult(
                    value_1=text_fragment,
                    value_2=None,
                    score=0.0
                ))
            mismatch_start_index = index + 1
            continue
        if match_start_index < index:
            text_fragment = TextFragment(text=haystack_str[match_start_index:index])
            result.append(FuzzyTextFragmentMatchResult(
                value_1=text_fragment,
                value_2=text_fragment,
                score=1.0
            ))
        match_start_index = index + 1
    if mismatch_start_index < len(haystack_str):
        text_fragment = TextFragment(text=haystack_str[mismatch_start_index:])
        result.append(FuzzyTextFragmentMatchResult(
            value_1=text_fragment,
            value_2=None,
            score=0.0
        ))
    if match_start_index < len(haystack_str):
        text_fragment = TextFragment(text=haystack_str[match_start_index:])
        result.append(FuzzyTextFragmentMatchResult(
            value_1=text_fragment,
            value_2=text_fragment,
            score=1.0
        ))
    return result


def strip_whitespace(text: str) -> str:
    return re.sub(r'\s+', '', text)


def get_character_based_match_score_for_score(
    score: float,
    expected: AnyStr,
    actual: AnyStr,
    include_values: bool
) -> MatchScore:
    expected_str = str(expected) if expected else ''
    actual_str = str(actual) if actual else ''
    match_score = get_match_score_for_score(
        score=score,
        expected=expected_str,
        actual=actual_str,
        include_values=include_values
    )
    expected_without_whitespace_str = strip_whitespace(expected_str)
    expected_without_whitespace_len = len(expected_without_whitespace_str)
    actual_without_whitespace_str = strip_whitespace(actual_str)
    actual_without_whitespace_len = len(actual_without_whitespace_str)
    # true postive: a match (we can use the exepected count, same as actual)
    # false negative: mismatch, no actual value (use expected count)
    # false positive: mismatch, no expected value (use actual count)
    # true negative: nothing expected, no actual (not relevant in our case)
    match_score.true_positive *= expected_without_whitespace_len
    match_score.false_positive *= actual_without_whitespace_len
    match_score.false_negative *= expected_without_whitespace_len
    match_score.true_negative = 0
    LOGGER.debug('match_score: %s (expected=%r, actual=%r)', match_score, expected, actual)
    return match_score


class DeletedTextEvaluation(CustomEvaluation):
    def score(
        self,
        expected: List[str],
        actual: List[str],
        include_values: bool = True
    ) -> MatchScore:
        if expected and actual:
            match_results = get_fuzzy_matched_text_fragments(
                expected,
                actual
            )
            LOGGER.debug('match_results: %s', match_results)
            match_scores: List[MatchScore] = []
            for match_result in match_results:
                if not match_result.value_1:
                    # ignore extra text
                    continue
                match_scores.append(get_character_based_match_score_for_score(
                    score=match_result.score,
                    expected=match_result.value_1,
                    actual=match_result.value_2,
                    include_values=include_values
                ))
            template_match_score = get_match_score_for_score(
                expected=expected,
                actual=actual,
                score=safe_mean([
                    _score.score for _score in match_scores
                ]) if match_scores else 1.0,
                include_values=include_values
            )
            result_match_score = combine_partial_match_scores(
                match_scores,
                template_match_score
            )
        else:
            result_match_score = get_character_based_match_score_for_score(
                expected='\n'.join(expected),
                actual='\n'.join(actual),
                score=0.0,
                include_values=include_values
            )
        LOGGER.debug('result_match_score: %s', result_match_score)
        return result_match_score
