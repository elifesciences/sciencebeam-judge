import logging
import re
from collections import deque
from functools import partial
from typing import AnyStr, Deque, List, NamedTuple, Optional, Tuple,  T

from sciencebeam_alignment.align import LocalSequenceMatcher, SimpleScoring

from sciencebeam_judge.utils.seq_matching import (
    IndexRange,
    MatchingBlocks,
    MatchingBlocksWithMatchedText,
    StringView,
    FuzzyMatchResult,
    space_is_junk,
    get_first_chunk_matching_blocks,
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


# the number of gaps to add after unmatched characters
# this is to make the alignment aware of the gap after masking
UNMATCHED_GAP_PADDING = 2

MIN_TEXT_SPLIT_LENGTH = 2
MAX_TEXT_SPLIT_COUNT = 2


def combine_partial_match_scores(
    scores: List[MatchScore],
    template_score: MatchScore
):
    return MatchScore.from_dict(_combine_partial_match_scores(
        [score.to_dict() for score in scores],
        template_score.to_dict()
    ))


class FuzzyWrappedValue(WrappedValue):
    split_count: int = 0

    def __init__(self, *args, split_count: int = 0, **kwargs):
        super().__init__(*args, **kwargs)
        self.split_count = split_count

    def __getitem__(self, key) -> 'FuzzyWrappedValue':
        return FuzzyWrappedValue(
            self.value[key],
            index=self.index,
            split_count=self.split_count + 1
        )

    def strip(self) -> 'FuzzyWrappedValue':
        return FuzzyWrappedValue(
            self.value.strip(),
            index=self.index,
            split_count=self.split_count
        )


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


def expand_start_index_to_token(text: str, index: int) -> int:
    while index >= 1 and not text[index - 1].isspace():
        index -= 1
    return index


def expand_end_index_to_token(text: str, index: int) -> int:
    while index < len(text) and not text[index - 1].isspace():
        index += 1
    return index


def expand_index_range_to_token(text: str, index_range: IndexRange) -> IndexRange:
    return IndexRange((
        expand_start_index_to_token(text, index_range[0]),
        expand_end_index_to_token(text, index_range[1]),
    ))


def get_match_score(
    fm: FuzzyMatchResult,
    value_2_view: StringView
) -> float:
    b_index_range = fm.matching_blocks.start_end_b
    translated_b_index_range = (
        value_2_view.original_index_at[b_index_range[0]],
        value_2_view.original_index_at[b_index_range[1] - 1] + 1
    )
    expanded_translated_b_index_range = expand_index_range_to_token(
        value_2_view.original_string,
        translated_b_index_range
    )
    expanded_view_b_index_range = IndexRange((
        value_2_view.view_index_at[expanded_translated_b_index_range[0]],
        value_2_view.view_index_at[expanded_translated_b_index_range[1] - 1] + 1
    ))
    LOGGER.debug(
        'b_index_range: %s -> %s -> %s -> %s',
        b_index_range, translated_b_index_range, expanded_translated_b_index_range,
        expanded_view_b_index_range
    )
    return fm.ratio_to(expanded_view_b_index_range.size)


def fill_list_between(list_: List[T], start: int, end: int, value: T):
    if end > start:
        list_[start:end] = [value] * (end - start)


def mark_spaces_between_matches_as_matched(
    matched_list: List[bool],
    text: str
):
    matched_space_index: Optional[int] = None
    was_matched: bool = False
    for index, (is_match, c) in enumerate(zip(matched_list, text)):
        if c.isspace():
            if was_matched and matched_space_index is None:
                matched_space_index = index
            continue
        if is_match and matched_space_index is not None:
            fill_list_between(matched_list, matched_space_index, index, True)
        was_matched = is_match
        matched_space_index = None


def get_fuzzy_matched_characters(
    haystack_str: str,
    needles: List[str],
    threshold: float
):  # pylint: disable=too-many-locals, too-many-statements
    if not haystack_str:
        return []
    wrapped_haystack_values = [
        FuzzyWrappedValue(value, index)
        for index, value in iter_regex_split_with_index(haystack_str, r'\n')
    ]
    wrapped_needles = [
        FuzzyWrappedValue(value, index)
        for index, value in enumerate(needles)
    ]
    distance_matches = get_distance_matches(
        wrapped_haystack_values,
        wrapped_needles,
        distance_measure=DISTANCE_MEASURE,
        threshold=threshold
    )
    # using separate mask (visible to alignmnt) and matched (used in the result)
    # additional we use placeholder chars for already matched text
    haystack_mask = [not c.isspace() for c in haystack_str]
    haystack_matched = [False] * len(haystack_str)
    haystack_view_chars = list(haystack_str)
    remaining_paired_sequences: Deque[FuzzyWrappedValue] = deque()
    remaining_unpaired_sequences: Deque[FuzzyWrappedValue] = deque()
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
    wrapped_haystack = FuzzyWrappedValue(haystack_str, 0)
    while remaining_paired_sequences or remaining_unpaired_sequences:
        if remaining_paired_sequences:
            # prioritise paired sequences, they will be faster to calculate
            value_1, value_2 = remaining_paired_sequences.popleft()
        else:
            value_1 = wrapped_haystack
            value_2 = remaining_unpaired_sequences.popleft()
        value_1_view = StringView(
            ''.join(haystack_view_chars[value_1.index:value_1.index + len(value_1)]),
            haystack_mask[value_1.index:value_1.index + len(value_1)]
        )
        value_2_view = StringView(str(value_2), [not c.isspace() for c in str(value_2)])
        LOGGER.debug(
            'value_1: %r (index: %s), value_2: %r',
            value_1_view, value_1.index, value_2_view
        )
        if not value_1_view or not value_2_view:
            LOGGER.debug('ignoring, either value 1 or value 2 are empty')
            continue
        if not str(value_1_view).strip() or not str(value_2_view).strip():
            LOGGER.debug('ignoring, either value 1 or value 2 are blank')
            continue
        sm = LocalSequenceMatcher(
            str(value_1_view),
            str(value_2_view),
            DEFAULT_SCORING
        )
        original_matching_blocks = MatchingBlocks(sm.get_matching_blocks()).non_empty
        matching_blocks = get_first_chunk_matching_blocks(
            str(value_1_view),
            str(value_2_view),
            original_matching_blocks,
            threshold=0.6,
            is_junk_fn=space_is_junk,
            match_score_fn=partial(
                get_match_score,
                value_2_view=value_2_view
            )
        )
        LOGGER.debug(
            'matching_blocks: %s (original: %s)',
            MatchingBlocksWithMatchedText(matching_blocks, str(value_1_view)),
            MatchingBlocksWithMatchedText(original_matching_blocks, str(value_1_view))
        )
        if not matching_blocks:
            # no match
            if value_1 != wrapped_haystack:
                # try on the whole sequence again
                remaining_unpaired_sequences.append(value_2)
            continue
        matching_blocks = translate_string_view_matching_blocks(
            matching_blocks,
            value_1_view,
            value_2_view
        )
        matching_blocks = matching_blocks.with_offset(value_1.index, 0)
        LOGGER.debug(
            'translated matching_blocks: %s',
            MatchingBlocksWithMatchedText(matching_blocks, str(value_1))
        )
        for ai, _, size in matching_blocks:
            haystack_matched[ai:ai + size] = [True] * size
        a_start_offset = expand_start_index_to_token(
            haystack_str,
            matching_blocks.start_a
        )
        a_end_offset = matching_blocks.end_a
        # hide matched chars from being matched again
        fill_list_between(haystack_view_chars, a_start_offset, a_end_offset, ' ')
        # adding additional padding to take into account the distance between the characters
        fill_list_between(
            haystack_mask,
            a_start_offset + UNMATCHED_GAP_PADDING,
            a_end_offset - UNMATCHED_GAP_PADDING,
            False
        )

        b_start_offset = matching_blocks.start_b
        if b_start_offset:
            remaining_text = value_2[:b_start_offset].strip()
            LOGGER.debug('b_start_offset: %s (%r)', b_start_offset, remaining_text)
            if (
                len(remaining_text) > MIN_TEXT_SPLIT_LENGTH
                and remaining_text.split_count <= MAX_TEXT_SPLIT_COUNT
            ):
                remaining_unpaired_sequences.append(remaining_text)
        b_end_offset = matching_blocks.end_b
        if b_end_offset < len(value_2):
            remaining_text = value_2[b_end_offset:].strip()
            LOGGER.debug('b_end_offset: %s (%r)', b_end_offset, remaining_text)
            if (
                len(remaining_text) > MIN_TEXT_SPLIT_LENGTH
                and remaining_text.split_count <= MAX_TEXT_SPLIT_COUNT
            ):
                remaining_unpaired_sequences.append(remaining_text)
    mark_spaces_between_matches_as_matched(
        haystack_matched,
        haystack_str
    )
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
