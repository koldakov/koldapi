from __future__ import annotations

import traceback
from typing import TYPE_CHECKING, ClassVar

from koldapi.datastructures import Status
from koldapi.responses import PlainTextResponse

from .base import MiddlewareBase

if TYPE_CHECKING:
    from koldapi._types import ASGIApp, Receive, Scope, Send
    from koldapi.configs import Config


class ServerErrorMiddleware(MiddlewareBase):
    """
    Middleware that catches unhandled exceptions during request processing.

    In debug mode, it returns the traceback as plain text in the response.
    Otherwise, the exception is re-raised and passed to the server, which
    should generate a generic error response (usually 500).

    Attributes:
        status_code: Status code to return.
    """

    status_code: ClassVar[Status] = Status.HTTP_500_INTERNAL_SERVER_ERROR

    def __init__(self, app: ASGIApp, config: Config, /) -> None:
        """
        Initialize the middleware.

        Args:
            app: The next ASGI application in the stack.
            config: Application configuration.
        """
        super().__init__(app)
        self.config: Config = config

    async def _debug_response(self, scope: Scope, receive: Receive, send: Send, /) -> None:
        """
        Send a plain-text traceback response to the client.

        Args:
            scope: ASGI connection scope.
            receive: ASGI receive channel.
            send: ASGI send channel.
        """
        response: PlainTextResponse = PlainTextResponse(
            content=traceback.format_exc(),
            status_code=self.status_code,
        )

        await response(scope, receive, send)

    async def dispatch(self, scope: Scope, receive: Receive, send: Send, /) -> None:
        """
        Execute the request through the wrapped application.

        If an exception is raised and debug mode is enabled,
        a traceback response is returned. Otherwise, the exception
        is re-raised to let the server handle it.

        Args:
            scope: ASGI connection scope.
            receive: ASGI receive channel.
            send: ASGI send channel.
        """
        try:
            return await self.app(scope, receive, send)
        except Exception:
            if self.config.debug:
                await self._debug_response(scope, receive, send)
            raise
