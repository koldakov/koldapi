from __future__ import annotations

import inspect
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from types import AsyncGeneratorType
from typing import TYPE_CHECKING, Any, Self, TypeVar

from .datastructures import Method, State
from .routing import BaseRoute, Route, Router

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Callable

    from ._types import DecoratedCallable, Lifespan, Receive, Scope, Send
    from .configs import Config

AppType = TypeVar("AppType", bound="KoldAPI")


class KoldAPIBaseError(Exception):
    """KoldAPI Base Error."""


class LifespanYieldMissingError(KoldAPIBaseError):
    """Lifespan Yield Missing Error."""


class LifespanIsNotAsyncGeneratorError(KoldAPIBaseError):
    """Lifespan Is Not Async Generator Error."""


class LifespanYieldedMultipleTimesError(KoldAPIBaseError):
    """Lifespan Yielded Multiple Times Error."""


class KoldAPI(ABC):
    def __init__(self: AppType):
        self.app_config: Config = self.setup()
        self.state: State = State()
        self.router: Router = Router(self.app_config, self._lifespan_context())

    @property
    def routes(self) -> list[BaseRoute]:
        return self.router.routes

    @abstractmethod
    def setup(self) -> Config:
        """Initiate the application with the provided configuration.

        Returns:
            ``koldapi.Config`` - application configuration.
        """

    async def lifespan(self, app: Self, /) -> AsyncGenerator[Any, None]:
        """
        Generator managing the application's lifespan.

        Performs setup tasks when the application starts and cleanup upon shutdown.

        Args:
            app: The application instance.

        Notes:
            Lifespan can yield only once.

        Example:
            >>> class MyShinyApp(KoldAPI):
            >>>     async def lifespan(self, app: Self, /) -> AsyncGenerator[dict[str, Any] | None, None]:
            >>>         # Actions before APP starts
            >>>         yield
            >>>         # Actions after APP shutdowns
            >>>
            >>>     def setup(self) -> Config:
            >>>         return Config()
            >>>
            >>>
            >>> # Or you can define anything that will get into request.app.state
            >>> class MyShinyAppWithState(KoldAPI):
            >>>     async def lifespan(self, app: Self, /) -> AsyncGenerator[dict[str, Any] | None, None]:
            >>>         # Setup: connect to the database
            >>>         yield {"db": await db.connect()}  # Yield control back to the app to run
            >>>
            >>>         # Teardown: disconnect from the database
            >>>         await app.state.db.disconnect()
            >>>
            >>>     def setup(self) -> Config:
            >>>         return Config()

        Yields:
            dict[str, Any] | None: Optional data passed during the application's lifespan.
            None: If no additional information is needed.
        """
        yield

    def get(
        self,
        path: str,
        /,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        return self._add_route(path, [Method.GET])

    def post(
        self,
        path: str,
        /,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        return self._add_route(path, [Method.POST])

    def put(
        self,
        path: str,
        /,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        return self._add_route(path, [Method.PUT])

    def delete(
        self,
        path: str,
        /,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        return self._add_route(path, [Method.DELETE])

    def head(
        self,
        path: str,
        /,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        return self._add_route(path, [Method.HEAD])

    def options(
        self,
        path: str,
        /,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        return self._add_route(path, [Method.OPTIONS])

    def trace(
        self,
        path: str,
        /,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        return self._add_route(path, [Method.TRACE])

    def _lifespan_context(self) -> Lifespan[Self]:
        """
        Wrap the user-defined ``lifespan`` coroutine into an async context manager.

        This method converts the ``lifespan`` async generator defined by the user
        into a standard `asynccontextmanager` that can be used by the router or
        ASGI server. It handles:

        - Applying returned resources to the application's state.
        - Ensuring that ``lifespan`` yields exactly once.
        - Raising custom errors if the generator yields multiple times or not at all.

        Returns:
            Lifespan[Self]: An async context manager that manages the application's
                lifespan resources and can be awaited by the ASGI router.

        Raises:
            LifespanYieldMissingError: If the user's ``lifespan`` generator does not yield.
            LifespanYieldedMultipleTimesError: If the user's ``lifespan`` yields more than once.
        """

        @asynccontextmanager
        async def manager(app: Self, /) -> AsyncGenerator[None, None]:
            lifespan_generator: AsyncGenerator[Any, None] = self.lifespan(app)

            if not isinstance(lifespan_generator, AsyncGeneratorType):
                if inspect.iscoroutine(lifespan_generator):
                    await lifespan_generator
                else:
                    raise LifespanIsNotAsyncGeneratorError()

                raise LifespanYieldMissingError()

            yielded: bool = False
            async for resources in lifespan_generator:
                if yielded:
                    raise LifespanYieldedMultipleTimesError()
                yielded = True
                if resources is not None:
                    for key, value in resources.items():
                        setattr(app.state, key, value)
                yield

        return manager

    def _add_route(
        self,
        path: str,
        methods: list[Method],
        /,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        """
        Register a new route with the given path and HTTP methods.

        Args:
            path: The URL path for the route (e.g., "/users").
            methods: HTTP method list.

        Returns:
            Callable[[DecoratedCallable], DecoratedCallable]: A decorator that,
            when applied to the endpoint, registers it as a route handler and
            returns the original function unchanged.
        """

        def decorator(func: DecoratedCallable, /) -> DecoratedCallable:
            self.router.add_route(Route(path, func, methods))
            return func

        return decorator

    def _populate_scope(self, scope: Scope, /) -> None:
        """
        Populate the scope with extra values.

        Args:
            scope: Static request information, such as request type (http, websocket), headers, etc.
        """
        scope["app"] = self

    async def __call__(self, scope: Scope, receive: Receive, send: Send, /) -> None:
        """
        Get the request and process it.

        Args:
            scope: Static request information, such as request type (http, websocket), headers, etc.
            receive: An awaitable callable that yields incoming events/messages from the client or server.
            send: An awaitable callable used to send events/messages back to the client or server.
        """
        self._populate_scope(scope)
        await self.router(scope, receive, send)
