from unittest.mock import AsyncMock

import pytest

from koldapi import Config, KoldAPI
from koldapi.applications import (
    LifespanIsNotAsyncGeneratorError,
    LifespanYieldedMultipleTimesError,
    LifespanYieldMissingError,
)


class SimpleApp(KoldAPI):
    def setup(self) -> Config:
        return Config()


class TestApplication:
    def setup_method(self):
        self.app = SimpleApp()

    @pytest.mark.asyncio
    async def test_lifespan_yield_none(self):
        async with self.app._lifespan_context()(self.app):
            pass

    @pytest.mark.asyncio
    async def test_lifespan_yield_state(self):
        class AppWithState(SimpleApp):
            async def lifespan(self, _):
                yield {"db": "connected"}

        app = AppWithState()
        async with app._lifespan_context()(app):
            assert app.state.db == "connected"

    @pytest.mark.asyncio
    async def test_lifespan_yield_missing_error(self):
        class AppWithNotAsyncGeneratorLifespan(SimpleApp):
            def lifespan(self, _):
                yield

        app = AppWithNotAsyncGeneratorLifespan()
        with pytest.raises(LifespanIsNotAsyncGeneratorError):
            async with app._lifespan_context()(app):
                pass

    @pytest.mark.asyncio
    async def test_lifespan_yield_multiple_times_error(self):
        class AppWIthMultipleLifespanYields(SimpleApp):
            async def lifespan(self, _):
                yield
                yield

        app = AppWIthMultipleLifespanYields()
        with pytest.raises(LifespanYieldedMultipleTimesError):
            async with app._lifespan_context()(app):
                pass

    @pytest.mark.asyncio
    async def test_lifespan_is_not_async_generator_error(self):
        class AppWithoutLifespanYield(SimpleApp):
            async def lifespan(self, _):
                return

        app = AppWithoutLifespanYield()
        with pytest.raises(LifespanYieldMissingError):
            async with app._lifespan_context()(app):
                pass

    def test_get_should_add_route(self):
        @self.app.get("/test")
        async def foo():
            pass

        assert len(self.app.routes) == 1

    def test_post_should_add_route(self):
        @self.app.post("/test")
        async def foo():
            pass

        assert len(self.app.routes) == 1

    def test_put_should_add_route(self):
        @self.app.put("/test")
        async def foo():
            pass

        assert len(self.app.routes) == 1

    def test_delete_should_add_route(self):
        @self.app.delete("/test")
        async def foo():
            pass

        assert len(self.app.routes) == 1

    def test_head_should_add_route(self):
        @self.app.head("/test")
        async def foo():
            pass

        assert len(self.app.routes) == 1

    def test_options_should_add_route(self):
        @self.app.options("/test")
        async def foo():
            pass

        assert len(self.app.routes) == 1

    def test_trace_should_add_route(self):
        @self.app.trace("/test")
        async def foo():
            pass

        assert len(self.app.routes) == 1

    @pytest.mark.asyncio
    async def test_app_call_should_call_router(self):
        scope = {"type": "http"}
        receive = AsyncMock()
        send = AsyncMock()

        self.app._middleware_stack = AsyncMock()

        await self.app(scope, receive, send)

        assert scope["app"] is self.app
        self.app._middleware_stack.assert_awaited_once_with(scope, receive, send)
