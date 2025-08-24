from unittest.mock import AsyncMock

import pytest

from koldapi import Receive, Scope, Send
from koldapi.middleware import MiddlewareBase, NextMiddleware


class TestMiddlewareBase:
    def setup_method(self):
        class SimpleMiddleware(MiddlewareBase):
            async def dispatch(self, scope: Scope, receive: Receive, send: Send, /) -> None:
                scope["simple_app"] = True

        self.simple_middleware = SimpleMiddleware
        self.receive = AsyncMock()
        self.send = AsyncMock()

    @pytest.mark.asyncio
    async def test_middleware_base_calls_dispatch(self):
        scope = {"type": "http"}

        async def dummy_app(_scope, _receive, _send):
            _scope["called_app"] = True

        middleware = self.simple_middleware(dummy_app)
        await middleware(scope, self.receive, self.send)

        assert scope.get("simple_app") is True
        assert scope.get("called_app") is None


class TestMiddleware:
    def setup_method(self):
        class LoggingMiddleware(NextMiddleware):
            async def dispatch(self, scope: Scope, receive: Receive, send: Send, /) -> None:
                scope["logged"] = True

        self.middleware = LoggingMiddleware
        self.receive = AsyncMock()
        self.send = AsyncMock()

    @pytest.mark.asyncio
    async def test_next_middleware_calls_app(self):
        scope = {"type": "http"}
        called_app = False

        async def dummy_app(_scope, _receive, _send):
            nonlocal called_app
            called_app = True

        middleware = self.middleware(dummy_app)
        await middleware(scope, self.receive, self.send)

        assert scope["logged"] is True
        assert called_app is True
