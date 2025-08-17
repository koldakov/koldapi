from __future__ import annotations

from collections.abc import Iterator, MutableMapping
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from koldapi._types import Scope


class Headers(MutableMapping[str, str]):
    """
    A case-insensitive HTTP headers container.
    """

    # According to the ISO-8859-1 standard headers shall be in latin-1 encoding.
    # However, ASGI servers can accept and handle other encoding such as UTF-8.
    _encoding: ClassVar[str] = "latin-1"

    def __init__(self, headers: dict[str, str] | None = None) -> None:
        self._store: dict[str, str] = {}
        self._set_headers(headers)

        self._raw: list[tuple[bytes, bytes]] | None = None

    @classmethod
    def from_scope(cls, scope: Scope, /) -> Headers:
        """
        Create Headers instance from ASGI scope.

        Args:
            scope: ASGI scope dictionary containing headers.

        Returns:
            Headers: A new Headers instance populated with headers from the scope.
        """
        raw_headers = scope.get("headers", [])
        decoded_headers = {k.decode(cls._encoding): v.decode(cls._encoding) for k, v in raw_headers}
        return cls(decoded_headers)

    def _set_headers(self, headers: dict[str, str] | None) -> None:
        """
        Set the headers.

        Args:
            headers: Provided headers.
        """
        if headers is None:
            return
        for k, v in headers.items():
            self[k] = v

    @property
    def raw(self) -> list[tuple[bytes, bytes]]:
        """
        Return headers in ASGI raw format.
        """
        if self._raw is None:
            self._raw = [(k.encode(self._encoding), v.encode(self._encoding)) for k, v in self._store.items()]

        return self._raw

    def __getitem__(self, key: str, /) -> str:
        return self._store[key.lower()]

    def __setitem__(self, key: str, value: str, /) -> None:
        self._store[key.lower()] = value
        self._raw = None

    def __delitem__(self, key: str, /) -> None:
        del self._store[key.lower()]
        self._raw = None

    def __iter__(self) -> Iterator[str]:
        return iter(self._store)

    def __len__(self) -> int:
        return len(self._store)

    def __contains__(self, key: Any, /) -> bool:
        if not isinstance(key, str):
            return False
        return key.lower() in self._store
