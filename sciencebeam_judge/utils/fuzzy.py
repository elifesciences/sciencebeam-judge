import logging

from typing import AnyStr, Callable, Iterable, List, Optional, Tuple


LOGGER = logging.getLogger(__name__)


T_IsJunkFunction = Callable[[AnyStr, int], bool]


class StringView:
    def __init__(self, original_string: str, in_view: List[bool]):
        self.original_string = original_string
        self.in_view = in_view
        self.string_view = ''.join((
            ch
            for ch, is_included in zip(original_string, in_view)
            if is_included
        ))
        self.original_index_at = [
            index
            for index, is_included in enumerate(in_view)
            if is_included
        ]
        self._view_index_at: Optional[List[int]] = None

    @staticmethod
    def from_view_map(original_string: str, in_view: List[bool]) -> 'StringView':
        return StringView(original_string, in_view)

    @property
    def view_index_at(self) -> List[int]:
        if self._view_index_at is not None:
            return self._view_index_at
        view_index_at = []
        index = 0
        for is_included in self.in_view:
            view_index_at.append(index)
            if is_included:
                index += 1
        self._view_index_at = view_index_at
        return view_index_at

    def __len__(self):
        return len(self.string_view)

    def __str__(self):
        return self.string_view

    def __repr__(self):
        return '%s(original=%r, in_view=%s, view=%r)' % (
            type(self).__name__, self.original_string, self.in_view, self.string_view
        )


class IndexRange(Tuple[int, int]):
    @property
    def size(self):
        return self[1] - self[0]


class MatchingBlocks(Tuple[Tuple[int, int, int], ...]):
    def with_offset(self, a_offset: int, b_offset: int) -> 'MatchingBlocks':
        if not a_offset and not b_offset:
            return self
        return MatchingBlocks(tuple(
            (ai + a_offset, bi + b_offset, size)
            for ai, bi, size in self
        ))

    @property
    def non_empty(self) -> 'MatchingBlocks':
        return MatchingBlocks(tuple(
            (ai, bi, size)
            for ai, bi, size in self
            if size
        ))

    @property
    def first_block(self) -> Optional[Tuple[int, int, int]]:
        if not self:
            return None
        first_block = self[0]
        first_block_size = first_block[2]
        if first_block_size:
            return first_block
        return None

    @property
    def last_block(self) -> Optional[Tuple[int, int, int]]:
        index = len(self) - 1
        while index >= 0:
            last_block = self[index]
            last_block_size = last_block[2]
            if last_block_size:
                return last_block
            index -= 1
        return None

    def get_start_offset(self, seq_index: int):
        first_block = self.first_block
        if not first_block:
            return None
        return first_block[seq_index]

    @property
    def start_a(self):
        return self.get_start_offset(0)

    @property
    def start_b(self):
        return self.get_start_offset(1)

    def get_end_offset(self, seq_index: int) -> int:
        last_block = self.last_block
        if not last_block:
            return 0
        last_block_size = last_block[2]
        return last_block[seq_index] + last_block_size

    @property
    def end_a(self):
        return self.get_end_offset(0)

    @property
    def end_b(self):
        return self.get_end_offset(1)

    @property
    def start_end_a(self) -> IndexRange:
        return IndexRange((self.start_a, self.end_a,))

    @property
    def start_end_b(self) -> IndexRange:
        return IndexRange((self.start_b, self.end_b,))

    @property
    def match_count(self) -> int:
        return sum(size for _, _, size in self)


class MatchingBlocksWithMatchedText:
    def __init__(self, matching_blocks: Tuple[Tuple[int, int, int], ...], text: str):
        self.matching_blocks = matching_blocks
        self.text = text

    def __iter__(self) -> Iterable[Tuple[int, int, int, str]]:
        return (
            (a_index, b_index, size, self.text[a_index:a_index + size])
            for a_index, b_index, size in self.matching_blocks
        )

    def __repr__(self):
        return str(tuple(self))


def iter_translate_string_view_matching_block(
    a_index: int,
    b_index: int,
    size: int,
    a_string_view: StringView,
    b_string_view: StringView
) -> Iterable[Tuple[int, int, int]]:
    if not size:
        return
    remaining_view_size = size
    view_block_size = remaining_view_size
    while view_block_size:
        a_original_index = a_string_view.original_index_at[a_index]
        b_original_index = b_string_view.original_index_at[b_index]
        a_original_size = (
            a_string_view.original_index_at[a_index + view_block_size - 1]
            - a_original_index
            + 1
        )
        b_original_size = (
            b_string_view.original_index_at[b_index + view_block_size - 1]
            - b_original_index
            + 1
        )
        if a_original_size != b_original_size:
            LOGGER.debug('a_size: %d, b_size: %d', a_original_size, b_original_size)
            view_block_size -= 1
            continue
        yield a_original_index, b_original_index, a_original_size
        a_index += view_block_size
        b_index += view_block_size
        remaining_view_size -= view_block_size
        view_block_size = remaining_view_size


def translate_string_view_matching_blocks(
    matching_blocks: MatchingBlocks,
    a_string_view: StringView,
    b_string_view: StringView
) -> MatchingBlocks:
    return MatchingBlocks([
        (a_view_index, b_view_index, view_size)
        for ai, bi, size in matching_blocks
        for a_view_index, b_view_index, view_size in iter_translate_string_view_matching_block(
            ai, bi, size, a_string_view=a_string_view, b_string_view=b_string_view
        )
    ])


def space_is_junk(text: str, index: int) -> bool:
    return text[index].isspace()


class FuzzyMatchResult:
    def __init__(
        self,
        a: str,
        b: str,
        matching_blocks: MatchingBlocks,
        is_junk_fn: Optional[T_IsJunkFunction] = None
    ):
        self.a = a
        self.b = b
        self.matching_blocks = matching_blocks
        self.non_empty_matching_blocks = matching_blocks.non_empty
        self.is_junk_fn = is_junk_fn

    def __repr__(self):
        return (
            '{}(matching_blocks={}, match_count={}, a_length={}, b_length={})'.format(
                type(self).__name__,
                self.matching_blocks,
                self.matching_blocks.match_count,
                len(self.a),
                len(self.b)
            )
        )

    def ratio_to(self, size: int) -> float:
        if not size:
            return 0.0
        return self.matching_blocks.match_count / size


def get_first_chunk_matching_blocks(
    haystack: str,
    needle: str,
    matching_blocks: MatchingBlocks,
    threshold: float,
    is_junk_fn: T_IsJunkFunction,
    match_score_fn: Callable[[FuzzyMatchResult], float]
) -> MatchingBlocks:
    matching_blocks = matching_blocks.non_empty
    block_count = len(matching_blocks)
    while block_count:
        chunk_matching_blocks = MatchingBlocks(matching_blocks[:block_count])
        chunk_needle_start = chunk_matching_blocks.start_b
        chunk_needle_end = chunk_matching_blocks.end_b
        LOGGER.debug(
            'chunk_needle_start: %s, chunk_needle_end: %s',
            chunk_needle_start, chunk_needle_end
        )
        if chunk_needle_end <= chunk_needle_start:
            break
        chunk_needle = needle[chunk_needle_start:chunk_needle_end]
        fm = FuzzyMatchResult(
            haystack,
            chunk_needle,
            chunk_matching_blocks,
            is_junk_fn=is_junk_fn
        )
        ratio = match_score_fn(fm)
        LOGGER.debug('temp fm: %s (ratio: %s)', fm, ratio)
        if ratio >= threshold:
            LOGGER.debug('chunk_needle: %s', chunk_needle)
            return chunk_matching_blocks
        block_count -= 1
    return []
