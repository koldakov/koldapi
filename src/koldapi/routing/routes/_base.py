from __future__ import annotations

import inspect
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any, ClassVar

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from koldapi._types import Receive, Scope, Send
    from koldapi.configs import Config
    from koldapi.requests import HTTPConnection
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


@dataclass
class ParamError:
    """
    Represents an error that occurred while trying to convert or validate a parameter
    passed to an endpoint. This can be used for path parameters, query parameters,
    or any other dynamically injected arguments.

    Attributes:
        loc: The location of the parameter, e.g., ["path", "user_id"] or ["query", "page"].
        msg: Human-readable error message describing what went wrong.
        type: A string identifying the type of error, e.g., "type_error.int".
    """

    loc: list[str]
    msg: str
    type: str


class InvalidPathParamsError(BaseRouteError):
    """
    Exception raised when one or more path parameters cannot be converted
    to the expected type.
    """

    def __init__(self, errors: list[ParamError]) -> None:
        """
        Args:
            errors: List of ParamError.
        """
        self.errors: list[ParamError] = errors
        super().__init__(self._format_errors())

    def _format_errors(self) -> str:
        return "; ".join(f"{err.loc}: {err.msg}" for err in self.errors)


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
        self.endpoint: Callable[..., Response | Awaitable[Response]] = endpoint

        self.endpoint_signature: inspect.Signature = inspect.signature(self.endpoint)

    @abstractmethod
    def matches(self, scope: Scope, /) -> tuple[Match, Scope]:
        """
        Match the give path with the route's path.

        Args:
            scope: ASGI server scope.

        Returns:
            Match type and scope.
        """

    def build_endpoint_kwargs(self, connection: HTTPConnection, /) -> dict[str, Any]:
        """
        Construct the argument list for an endpoint dynamically.

        Uses the path parameters from the connection scope and respects the type annotations
        declared by the user in the endpoint signature. Automatically casts each path
        parameter to the annotated type if provided, allowing endpoints to receive fully
        typed arguments without manual conversion.

        This method enables flexible, type-safe parameter injection for the endpoints.

        Notes:
            Here we build named arguments as people can ignore the order of arguments.

        Args:
            connection: Incoming connection.

        Raises:
            InvalidPathParamsError: if path parameters can't be cast to the requested type annotation.
        """
        path_params: dict[str, str] | None = connection.scope.get("path_params")
        if not path_params:
            return {}

        kwargs: dict[str, Any] = {}
        errors: list[ParamError] = []

        name: str
        param: inspect.Parameter
        for name, param in self.endpoint_signature.parameters.items():
            if name not in path_params:
                continue

            value = path_params[name]
            if param.annotation not in (inspect._empty, str):
                try:
                    value = param.annotation(value)
                except Exception:  # noqa: BLE001
                    errors.append(
                        ParamError(
                            loc=["path", name],
                            msg=f"Can't convert to {param.annotation.__name__}",
                            type=f"type_error.{param.annotation.__name__}",
                        )
                    )
            kwargs[name] = value

        if errors:
            raise InvalidPathParamsError(errors)

        return kwargs

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
