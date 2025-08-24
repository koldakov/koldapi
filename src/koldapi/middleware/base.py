from abc import ABC, abstractmethod
from typing import Generic, TypeVar

from koldapi._types import ASGIApp, Receive, Scope, Send


class MiddlewareBase(ABC):
    """
    Base class for all middleware in the KoldAPI framework.

    Middleware should subclass this and implement the `dispatch` method.
    It can perform pre-processing, post-processing, or handle exceptions.
    """

    def __init__(self, app: ASGIApp, /, *args, **kwargs) -> None:
        """
        Initialize the middleware with the next ASGI app in the chain.

        Args:
            app: The ASGI application or middleware to wrap.
            args: Optional additional positional arguments for subclasses.
            kwargs: Optional additional named arguments for subclasses.
        """
        self.app: ASGIApp = app

    @abstractmethod
    async def dispatch(self, scope: Scope, receive: Receive, send: Send, /) -> None:
        """
        Implement this method to add custom middleware logic.

        This is called before passing control to the next middleware/app.

        Args:
            scope: The ASGI connection scope.
            receive: Callable to receive ASGI events.
            send: Callable to send ASGI events.
        """

    async def __call__(self, scope: Scope, receive: Receive, send: Send, /) -> None:
        """
        ASGI entry point for the middleware.

        By default, calls `dispatch`.

        Args:
            scope: The ASGI connection scope.
            receive: Callable to receive ASGI events.
            send: Callable to send ASGI events.
        """
        await self.dispatch(scope, receive, send)


class NextMiddleware(MiddlewareBase, ABC):
    """
    Helper base class for middlewares that automatically call the next app in the chain.

    Use this if you want to implement middleware without manually calling `self.app`.
    """

    async def __call__(self, scope: Scope, receive: Receive, send: Send, /) -> None:
        """
        Call `dispatch` and then automatically forward the request to the next app.

        Args:
            scope: The ASGI connection scope.
            receive: Callable to receive ASGI events.
            send: Callable to send ASGI events.

        Examples:
            >>> from koldapi.middleware import NextMiddleware
            >>> from koldapi import Scope, Receive, Send

            >>> class LoggingMiddleware(NextMiddleware):
            >>>    # Simple middleware that logs each incoming request's path and method.
            >>>    # Automatically calls the next middleware or app after logging.
            >>>
            >>>    async def dispatch(self, scope: Scope, receive: Receive, send: Send, /) -> None:
            >>>        print(f"[LOG] Incoming request: {scope['method']} {scope['path']}")
            >>>        # No need to call self.app here — NextMiddleware will handle it
        """
        await super().__call__(scope, receive, send)
        await self.app(scope, receive, send)


T = TypeVar("T", bound="MiddlewareBase")


class Middleware(Generic[T]):
    """
    Wrapper for a middleware class that allows lazy instantiation with arguments.

    This is used to store middleware definitions and their constructor arguments,
    and instantiate them when building the middleware stack.
    """

    def __init__(self, cls: type[T], *args, **kwargs) -> None:
        """
        Store the middleware class and its constructor arguments.

        Args:
            cls: The middleware class to wrap.
            *args: Positional arguments to pass to the middleware constructor.
            **kwargs: Keyword arguments to pass to the middleware constructor.
        """
        self.cls: type[T] = cls
        self.args = args
        self.kwargs = kwargs

    def __call__(self, app: ASGIApp, /) -> T:
        """
        Instantiate the middleware with the given ASGI app.

        Args:
            app: The next ASGI app or middleware in the chain.

        Returns:
            An instance of the middleware wrapping the provided app.
        """
        return self.cls(app, *self.args, **self.kwargs)
