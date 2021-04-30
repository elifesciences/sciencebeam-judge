from typing import Optional, Tuple


class MatchingBlocks(Tuple[int, int, int]):
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
        if not self.last_block:
            return 0
        last_block_size = last_block[2]
        return last_block[seq_index] + last_block_size

    @property
    def end_a(self):
        return self.get_end_offset(0)

    @property
    def end_b(self):
        return self.get_end_offset(1)
