from __future__ import annotations

import inspect
import re
from abc import ABC, abstractmethod
from enum import StrEnum
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from koldapi._types import Receive, Scope, Send
    from koldapi.configs import Config
    from koldapi.requests import Request
    from koldapi.responses import Response


class Match(StrEnum):
    """
    Represents the result of a route matching attempt.

    Attributes:
        NONE: No match — the route's path does not match the incoming request.
        PARTIAL: Partial match — the route's path matches, but other criteria
                 (e.g., HTTP method) do not.
        FULL: Full match — both the route's path and all criteria match the request.
    """

    NONE = "NONE"
    PARTIAL = "PARTIAL"
    FULL = "FULL"


class BaseRouteError(Exception):
    """Base Route Error."""


class RouteWithMethodAlreadyDefinedError(BaseRouteError):
    """Route With Method Already Defined Error."""


class InvalidRequestTypeError(BaseRouteError):
    """Invalid Request Type Error."""


class BaseRoute(ABC):
    _param_regex: ClassVar[str] = r"{([a-zA-Z_][a-zA-Z0-9_]*)}"

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

        self._endpoint_signature: inspect.Signature = inspect.signature(self.endpoint)
        self.endpoint_args_dict: dict[str, inspect.Parameter] = {
            name: param.annotation for name, param in self._endpoint_signature.parameters.items()
        }

    @abstractmethod
    def matches(self, scope: Scope, /) -> tuple[Match, Scope]:
        """
        Match the give path with the route's path.

        Args:
            scope: ASGI server scope.

        Returns:
            Match type and scope.
        """

    def compile_path(self, path: str, /) -> tuple[re.Pattern[str], list[str]]:
        """
        Convert a path with path params into a regex pattern.

        Args:
            path: requested path.

        Example:
            "/users/{id}" -> ^/users/(?P<id>[^/]+)$

        Returns:
            Tuple of path pattern and parameter names.
        """
        param_names: list[str] = []

        def replace(match: re.Match, /) -> str:
            name: str = match.group(1)
            param_names.append(name)
            return f"(?P<{name}>[^/]+)"

        pattern: str = re.sub(self._param_regex, replace, path)
        return re.compile(f"^{pattern}$"), param_names

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
