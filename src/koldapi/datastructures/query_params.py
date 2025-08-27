from __future__ import annotations

from collections.abc import Iterator, Mapping
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs

if TYPE_CHECKING:
    from koldapi._types import Scope


class QueryParams(Mapping[str, list[str]]):
    _encoding: str = "latin-1"

    @classmethod
    def from_scope(cls, scope: Scope, /) -> QueryParams:
        query_string: str = scope["query_string"].decode(cls._encoding)
        return cls(parse_qs(query_string, keep_blank_values=True))

    def __init__(self, params: dict[str, list[str]]) -> None:
        self._dict: dict[str, list[str]] = params

    def __getitem__(self, key: str) -> list[str]:
        return self._dict[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._dict)

    def __len__(self) -> int:
        return len(self._dict)

    def __contains__(self, key: Any) -> bool:
        return key in self._dict
