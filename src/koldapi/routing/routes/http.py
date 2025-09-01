import inspect
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from koldapi._types import Receive, Scope, Send
from koldapi.configs import Config
from koldapi.datastructures import Method
from koldapi.requests import HTTPConnection, Request
from koldapi.responses import Response

from ._base import (
    BaseRoute,
    InvalidRequestTypeError,
    Match,
)

if TYPE_CHECKING:
    import re


class Route(BaseRoute):
    def __init__(self, path: str, endpoint: Callable, methods: list[Method], /) -> None:
        super().__init__(path, endpoint)
        self.methods: list[Method] = methods
        self.regex, self.param_names = self.compile_path(path)

    def matches(self, scope: Scope, /) -> tuple[Match, Scope]:
        match: re.Match[str] | None = self.regex.match(scope["path"])
        if not match:
            return Match.NONE, {}

        matched_path_params: dict[str, str] = match.groupdict()
        path_params: dict[str, str] = scope.get("path_params", {})
        path_params.update(matched_path_params)
        scope_: Scope = {"path_params": path_params}

        if scope["method"].upper() in self.methods:
            return Match.FULL, scope_

        return Match.PARTIAL, scope_

    def __add_request_kwarg(self, connection: HTTPConnection, kwargs: dict[str, Any], /) -> None:
        """
        Add request kwarg to the endpoint kwargs if needed.

        Args:
            connection: Incoming HTTP request.
            kwargs: Endpoint kwargs.

        Raises:
            InvalidRequestTypeError if provided connection type is not correct.
        """
        param: inspect.Parameter | None = self.endpoint_signature.parameters.get("request")
        if param is None:
            return

        if param.annotation not in (Request, inspect._empty):
            raise InvalidRequestTypeError(
                f"Got unexpected request type {param.annotation!r}. "
                "Expected `koldapi.requests.Request` or no type annotation."
            )

        kwargs.update({"request": connection})

    def build_endpoint_kwargs(self, connection: HTTPConnection, /) -> dict[str, Any]:
        kwargs: dict[str, Any] = super().build_endpoint_kwargs(connection)
        self.__add_request_kwarg(connection, kwargs)
        return kwargs

    async def _serve_endpoint(self, request: Request, /) -> Response:
        """
        Execute the endpoint with the given request and return a Response.

        If the endpoint returns an awaitable, it will be awaited.
        Otherwise, the result is assumed to be a Response and returned directly.

        Args:
            request: The Request object representing the incoming ASGI request.

        Returns:
            Response: The response produced by the endpoint, either directly
                      or by awaiting the endpoint if it is asynchronous.
        """
        response: Response | Awaitable[Response] = self.endpoint(**self.build_endpoint_kwargs(request))
        if inspect.isawaitable(response):
            return await response

        return response

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

        Raises:
            Exception: in there is an error in the endpoint.
                Should be caught in the middleware and
        """
        request: Request = Request(scope, receive)
        try:
            response: Response = await self._serve_endpoint(request)
        except Exception:
            raise

        await response(scope, receive, send)
