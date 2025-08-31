import inspect
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from koldapi._types import Receive, Scope, Send
from koldapi.configs import Config
from koldapi.datastructures import Method
from koldapi.requests import Request
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

    def __add_request_arg(self, request: Request, args: list[Any], /) -> None:
        """
        Add request arg to the endpoint args if needed.

        Args:
            request: Incoming HTTP request.
            args: Endpoint args list.

        Raises:
            InvalidRequestTypeError if provided request type is not correct.
        """
        param_type: inspect.Parameter | type[inspect._empty] | None = self.endpoint_args_dict.get("request")
        if param_type is None:
            return

        if param_type not in (Request, inspect._empty):
            raise InvalidRequestTypeError(
                f"Got unexpected request type {param_type!r}. "
                "Expected `koldapi.requests.Request` or no type annotation."
            )

        args.append(request)

    def _build_endpoint_args(self, request: Request, /) -> list[Any]:
        """

        Args:
            request: Incoming HTTP request.

        Returns:
            List of endpoint arguments.
        """
        args: list[Any] = []
        self.__add_request_arg(request, args)
        return args

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
        response: Response | Awaitable[Response] = self.endpoint(*self._build_endpoint_args(request))
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
