from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, Mock

import pytest

from koldapi import Config, Method
from koldapi.routing import BaseRoute, Route
from koldapi.routing.router import Router


class TestRouter:
    def setup_method(self):
        self.config = Config()

        # Simple mocks
        self.receive = AsyncMock()
        self.send = AsyncMock()

        async def send(message):
            self.sent_messages.append(message)

        self.send_messages = send
        self.sent_messages = []
        self.receive_calls = 0

        @asynccontextmanager
        async def lifespan(_):
            yield

        self.lifespan = lifespan

        self.router = Router(self.config, self.lifespan)
        self.route = Route("/test", AsyncMock(), [Method.GET])

    def test_add_route_should_append_new_route(self):
        @asynccontextmanager
        async def lifespan(_):
            yield

        router = Router(self.config, lifespan)
        router.add_route(Mock(spec=BaseRoute))

        assert len(router.routes) == 1

    @pytest.mark.asyncio
    async def test_call_should_process_lifespan_event_when_scope_type_is_lifespan(self):
        @asynccontextmanager
        async def lifespan(_):
            yield

        router = Router(self.config, lifespan)
        scope = {"type": "lifespan", "app": Mock()}

        await router(scope, self.receive, self.send)

    @pytest.mark.asyncio
    async def test_call_should_raise_not_implemented_error_when_scope_type_is_not_lifespan(self):
        @asynccontextmanager
        async def lifespan(_):
            yield

        router = Router(self.config, lifespan)
        scope = {"type": "http", "app": Mock()}

        with pytest.raises(NotImplementedError):
            await router(scope, self.receive, self.send)

    @pytest.mark.asyncio
    async def test_call_lifespan_sends_startup_and_shutdown_events(self):
        user_lifespan_action_before = AsyncMock()
        user_lifespan_action_after = AsyncMock()

        @asynccontextmanager
        async def mock_lifespan(app):
            await user_lifespan_action_before(app)
            yield
            await user_lifespan_action_after(app)

        async def receive():
            self.receive_calls += 1
            return {}

        async def send(message):
            self.sent_messages.append(message)

        router = Router(self.config, mock_lifespan)
        scope = {"type": "lifespan", "app": AsyncMock()}

        await router(scope, receive, send)

        assert self.sent_messages[0]["type"] == "lifespan.startup.complete"
        assert self.sent_messages[1]["type"] == "lifespan.shutdown.complete"
        user_lifespan_action_after.assert_awaited_once_with(scope["app"])
        user_lifespan_action_before.assert_awaited_once_with(scope["app"])
        assert self.receive_calls == 2

    @pytest.mark.asyncio
    async def test_call_lifespan_startup_failed(self):
        class CustomError(Exception): ...

        @asynccontextmanager
        async def mock_lifespan(_):
            raise CustomError("fail")
            yield

        async def receive():
            return {}

        router = Router(self.config, mock_lifespan)
        scope = {"type": "lifespan", "app": Mock()}

        with pytest.raises(CustomError):
            await router(scope, receive, self.send_messages)

        assert self.sent_messages[0]["type"] == "lifespan.startup.failed"
        assert "CustomError: fail" in self.sent_messages[0]["message"]

    @pytest.mark.asyncio
    async def test_call_lifespan_shutdown_failed(self):
        class CustomError(Exception): ...

        @asynccontextmanager
        async def mock_lifespan(_):
            yield
            raise CustomError("shutdown fail")

        async def receive():
            self.receive_calls += 1
            return {}

        router = Router(self.config, mock_lifespan)
        scope = {"type": "lifespan", "app": Mock()}

        with pytest.raises(CustomError):
            await router(scope, receive, self.send_messages)

        assert self.sent_messages[0]["type"] == "lifespan.startup.complete"
        assert self.sent_messages[1]["type"] == "lifespan.shutdown.failed"
        assert "CustomError: shutdown fail" in self.sent_messages[1]["message"]

    @pytest.mark.asyncio
    async def test_full_match_is_called(self):
        scope = {"type": "http", "path": "/test", "method": "GET"}
        self.router.add_route(self.route)

        await self.router(scope, self.receive, self.send)
        self.route.endpoint.assert_awaited_once()  # type: ignore[attr-defined]

    @pytest.mark.asyncio
    async def test_partial_match_is_called_if_partial(self):
        scope = {"type": "http", "path": "/test", "method": "POST"}
        self.router.add_route(self.route)

        with pytest.raises(NotImplementedError):
            await self.router(scope, self.receive, self.send)

    @pytest.mark.asyncio
    async def test_none_match_raises(self):
        scope = {"type": "http", "path": "/other", "method": "GET"}
        self.router.add_route(self.route)

        with pytest.raises(NotImplementedError):
            await self.router(scope, self.receive, self.send)
