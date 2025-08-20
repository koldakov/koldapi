from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from koldapi._types import Receive, Scope, Send
    from koldapi.configs import Config
    from koldapi.requests import Request
    from koldapi.responses import Response


class BaseRouteError(Exception):
    """Base Route Error."""


class RouteMethodDoesNotMatchError(BaseRouteError):
    """Route Method Does Not Match Error."""


class RouteWithMethodAlreadyDefinedError(BaseRouteError):
    """Route With Method Already Defined Error."""


class BaseRoute(ABC):
    def __init__(self, path: str, endpoint: Callable, /) -> None:
        """
        Abstract base class representing a route definition.

        Args:
            path: The URL pattern for this route (e.g., "/users/{id}").
            endpoint: The request handler function or coroutine
                that will be called when the route matches an incoming request.
        """
        self.path: str = path
        self.endpoint: Callable[[Request], Response | Awaitable[Response]] = endpoint

    @abstractmethod
    def matches(self, scope: Scope, /) -> bool:
        """
        Returns true if route matches the scope path.

        Args:
            scope: ASGI server scope.

        Returns:
            True if route matches the scope path and False otherwise.

        Raises:
            ``koldapi.routing.RouteMethodDoesNotMatchError`` if scope HTTP method does not match
            with the path HTTP method.
        """

    @abstractmethod
    async def __call__(
        self,
        config: Config,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        """
        Serve an incoming ASGI request for the current route.

        Args:
            scope: The ASGI connection scope containing request details
                (type, path, headers, method, etc.).
            receive: Awaitable callable to receive ASGI events from the server.
            send: Awaitable callable to send ASGI events back to the server.
            config: Application configuration instance,
                providing settings and dependencies for the request lifecycle.
        """
