import logging
import re
from typing import AnyStr, List, NamedTuple

from sciencebeam_alignment.align import LocalSequenceMatcher, SimpleScoring

from sciencebeam_judge.evaluation.math import safe_mean

from sciencebeam_judge.evaluation.scoring_types.list import (
    _combine_partial_match_scores
)

from sciencebeam_judge.evaluation.custom import CustomEvaluation
from sciencebeam_judge.evaluation.match_scoring import MatchScore, get_match_score_for_score


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


def get_fuzzy_matched_characters(haystack_str, needles, threshold):
    if not haystack_str:
        return []
    haystack_matched = [False] * len(haystack_str)
    for needle in needles:
        if not needle:
            continue
        sm = LocalSequenceMatcher(haystack_str, needle, DEFAULT_SCORING)
        mb = sm.get_matching_blocks()
        match_count = sum(size for _, _, size in mb)
        match_ratio = match_count / len(needle)
        LOGGER.debug(
            'match_count=%d, match_ratio=%s, needle=%s',
            match_count, match_ratio, needle
        )
        if match_ratio < threshold:
            continue
        for ai, _, size in mb:
            haystack_matched[ai:ai + size] = [True] * size
    return haystack_matched


def get_fuzzy_matched_text_fragments(
    expected: List[str],
    actual: List[str]
) -> List[FuzzyTextFragmentMatchResult]:
    haystack_str = '\n'.join(expected)
    needles = actual
    threshold = 0.5
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
