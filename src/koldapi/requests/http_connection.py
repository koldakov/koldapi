from collections.abc import Iterator, Mapping
from typing import Any, ClassVar

from koldapi._types import Receive, Scope
from koldapi.datastructures import Headers, Method


class BaseHTTPConnection(Exception):
    """Base HTTP Connection."""


class WrongHTTPConnectionTypeError(BaseHTTPConnection):
    """Wrong HTTP Connection Type Error."""


class UnsupportedHTTPConnectionMethodError(BaseHTTPConnection):
    """Unsupported HTTP Connection Method Error."""


class HTTPConnection(Mapping[str, Any]):
    """
    Represents an HTTP connection in an ASGI application.

    Validates connection type on initialization and provides convenient
    access to scope data such as headers, path parameters, HTTP method, etc.

    Attributes:
        _allowed_types: Allowed ASGI connection types,
            e.g. "http" and "websocket".
    """

    _allowed_types: ClassVar[set[str]] = {
        "http",
        "websocket",
    }

    def __init__(self, scope: Scope, receive: Receive, /):
        """
        Initialize the HTTPConnection with the ASGI scope and receive callable.

        Args:
            scope: The ASGI connection scope dictionary.
            receive: The ASGI receive callable for incoming events.

        Raises:
            WrongHTTPConnectionTypeError: If the connection type is not allowed.
        """
        self._scope: Scope = scope
        self._receive: Receive = receive

        self._validate_connection()

        self._headers: Headers = Headers.from_scope(scope)

    def _validate_connection(self) -> None:
        """
        Validate the connection type against allowed types.

        Raises:
            WrongHTTPConnectionTypeError: If the connection type is unsupported.
        """
        if self._scope["type"] not in self._allowed_types:
            raise WrongHTTPConnectionTypeError(f'Connection type is not supported; type="{self._scope["type"]}"')

    @property
    def headers(self) -> Headers:
        """
        Return the request headers as a Headers object.

        Returns:
            The HTTP headers extracted from the ASGI scope.
        """
        return self._headers

    @property
    def path_params(self) -> dict[str, Any]:
        """
        Return the path parameters extracted from the ASGI scope.

        Returns:
            A dictionary of path parameters.
        """
        return self._scope.get("path_params", {})

    @property
    def app(self) -> Any:
        """
        Return the ASGI application instance associated with this connection.

        Returns:
            The ASGI app instance.
        """
        return self._scope["app"]

    @property
    def method(self) -> Method:
        """
        Return the HTTP method for this request.

        Returns:
            The HTTP method (e.g., ``Method.GET``, ``Method.POST``).
        """
        method: str = self._scope["method"]
        try:
            return Method(method.upper())
        except ValueError:
            raise UnsupportedHTTPConnectionMethodError() from None

    @property
    def scope(self) -> Scope:
        """
        Return the full ASGI connection scope dictionary.

        Returns:
            The ASGI scope.
        """
        return self._scope

    def receive(self) -> Receive:
        """
        Return the ASGI receive callable.

        Returns:
            The callable used to receive events from the client.
        """
        return self._receive

    def __getitem__(self, key: str) -> Any:
        return self._scope[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._scope)

    def __len__(self) -> int:
        return len(self._scope)
