import json
from json import JSONDecodeError
from typing import TYPE_CHECKING, Any, ClassVar

from koldapi._types import Receive, Scope

from .http_connection import BaseHTTPConnection, HTTPConnection

if TYPE_CHECKING:
    from collections.abc import MutableMapping


class WrongHTTPBodyFormatError(BaseHTTPConnection):
    """Wrong HTTP Body Format Error."""


class Request(HTTPConnection):
    """
    Represents an HTTP request connection.

    Extends HTTPConnection.
    """

    allowed_types: ClassVar[set[str]] = {
        "http",
    }

    def __init__(self, scope: Scope, receive: Receive, /) -> None:
        """
        Initialize the Request object with ASGI scope and receive callable.

        Args:
            scope: The ASGI connection scope dictionary.
            receive: The ASGI receive callable.
        """
        super().__init__(scope, receive)

        self._body: bytes | None = None
        self._json: dict[str, Any] | None = None

    async def body(self) -> bytes:
        """
        Collect the full HTTP request body.

        Reads the body from the ASGI receive channel in chunks until
        the entire body has been received (indicated by `more_body` flag).

        Caches the assembled body in `self._body` to avoid re-reading.

        Returns:
            The complete request body as bytes.
        """
        if self._body is not None:
            return self._body

        chunks: list[bytes] = []
        while True:
            message: MutableMapping[str, Any] = await self._receive()
            chunks.append(message.get("body", b""))
            if not message.get("more_body", False):
                break
        self._body = b"".join(chunks)
        return self._body

    async def json(self) -> dict[str, Any]:
        """
        Asynchronously parse and return the request body as JSON.

        If the JSON content has already been parsed and cached, returns
        the cached version to avoid redundant parsing.

        Returns:
            The parsed JSON object from the request body.

        Raises:
            WrongHTTPBodyFormatError: if body is not JSON serializable.
        """
        if self._json is not None:
            return self._json

        body: bytes = await self.body()
        try:
            self._json = json.loads(body)
        except JSONDecodeError:
            raise WrongHTTPBodyFormatError() from None
        return self._json
