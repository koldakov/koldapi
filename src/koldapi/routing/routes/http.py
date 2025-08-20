import inspect
from collections.abc import Awaitable, Callable

from koldapi._types import Receive, Scope, Send
from koldapi.configs import Config
from koldapi.datastructures import Method
from koldapi.requests import Request
from koldapi.responses import Response

from ._base import (
    BaseRoute,
)


class Route(BaseRoute):
    def __init__(self, path: str, endpoint: Callable, methods: list[Method], /) -> None:
        super().__init__(path, endpoint)
        self.methods: list[Method] = methods

    def matches(self, scope: Scope, /) -> bool:
        raise NotImplementedError()

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
        response: Response | Awaitable[Response] = self.endpoint(request)
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
