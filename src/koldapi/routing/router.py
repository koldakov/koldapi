import traceback
from typing import TYPE_CHECKING, Any

from koldapi._types import Lifespan, Receive, Scope, Send
from koldapi.configs import Config
from koldapi.routing.routes import BaseRoute

if TYPE_CHECKING:
    from collections.abc import Mapping
    from contextlib import AbstractAsyncContextManager


class Router:
    """
    Class represents the main entrypoint for each connection.
    The class gets the connection and routes the connection to the corresponding route.

    There are different connection types, such as http, websocket, lifespan.
    Lifespan is not a route directly, but still router handles this type of connection,
    because router is not linked to routes directly, it handles the connection itself.
    """

    def __init__(
        self,
        config: Config,
        lifespan_context: Lifespan[Any],
        /,
        *,
        routes: list[BaseRoute] | None = None,
    ) -> None:
        self.config: Config = config
        self.routes: list[BaseRoute] = routes or []
        self.lifespan_context: Lifespan[Any] = lifespan_context

    def add_route(self, route: BaseRoute, /) -> None:
        """
        Add a route to the router.

        Args:
            route: The route to be added.
        """
        self.routes.append(route)

    async def _lifespan(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
        /,
    ) -> None:
        """
        Handle lifespan event.

        Args:
            scope: The ASGI connection scope containing request details
                (type, path, headers, method, etc.).
            receive: Awaitable callable to receive ASGI events from the server.
            send: Awaitable callable to send ASGI events back to the server.
        """
        await receive()

        context_manager: AbstractAsyncContextManager[Mapping[str, Any] | None] = self.lifespan_context(scope["app"])

        try:
            await context_manager.__aenter__()
        except BaseException:
            await send(
                {
                    "type": "lifespan.startup.failed",
                    "message": traceback.format_exc(),
                }
            )
            raise
        else:
            await send({"type": "lifespan.startup.complete"})

        await receive()

        try:
            await context_manager.__aexit__(None, None, None)
        except BaseException:
            await send(
                {
                    "type": "lifespan.shutdown.failed",
                    "message": traceback.format_exc(),
                }
            )
            raise
        else:
            await send({"type": "lifespan.shutdown.complete"})

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
        /,
    ) -> None:
        """
        ASGI entry point for handling all types of connections.

        Depending on the connection type (scope["type"]), it dispatches the
        request to the appropriate handler.

        Args:
            scope: The ASGI connection scope containing request details
                (type, path, headers, method, etc.).
            receive: Awaitable callable to receive ASGI events from the server.
            send: Awaitable callable to send ASGI events back to the server.
        """
        scope.setdefault("router", self)

        event_type: str = scope["type"]
        if event_type == "lifespan":
            await self._lifespan(scope, receive, send)
            return

        raise NotImplementedError()
