from typing import Union
from typing_extensions import Protocol


class StrLikeProtocol(Protocol):
    def __str__(self) -> str:
        pass


StrLike = Union[str, StrLikeProtocol]
