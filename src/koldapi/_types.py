"""
This module defines core type aliases and abstractions for an ASGI-like framework.

- `Scope`: Represents a connection scope, which is a mutable mapping containing
  information about a protocol connection (e.g., HTTP, WebSocket) and persists
  for the lifetime of the connection.

- `Message`: Represents an event message in the ASGI protocol. It is a mutable
  mapping that can hold arbitrary data sent or received through the connection.

- `Receive`: An awaitable callable used to receive messages from the server
  or client.

- `Send`: An awaitable callable used to send messages to the server or client.

- `ASGIApp`: Anything that accepts `Scope`, `Receive` and `Send`.

- `StatelessLifespan`: A callable that receives an application instance and
  returns an asynchronous context manager that does not yield any state.
  Used to manage the application lifespan events without maintaining state.

- `StatefulLifespan`: A callable that receives an application instance and
  returns an asynchronous context manager that yields a mapping of state.
  Used for managing lifespan events while providing application-wide state.

- `Lifespan`: Union of `StatelessLifespan` and `StatefulLifespan`.

- `DecoratedCallable`: Generic type for a callable that can be decorated.

This module serves as a foundation for typing, connection handling, and lifespan
management in an ASGI-style framework, providing strong typing for asynchronous
operations and application lifecycle management.
"""

from collections.abc import Awaitable, Callable, Mapping, MutableMapping
from contextlib import AbstractAsyncContextManager
from typing import Any, TypeVar

AppType = TypeVar("AppType")

Scope = MutableMapping[str, Any]
Message = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]

ASGIApp = Callable[[Scope, Receive, Send], Awaitable[None]]

StatelessLifespan = Callable[[AppType], AbstractAsyncContextManager[None]]
StatefulLifespan = Callable[[AppType], AbstractAsyncContextManager[Mapping[str, Any]]]
Lifespan = StatelessLifespan[AppType] | StatefulLifespan[AppType]

DecoratedCallable = TypeVar("DecoratedCallable", bound=Callable[..., Any])
