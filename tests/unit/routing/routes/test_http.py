from unittest.mock import AsyncMock

import pytest

from koldapi import Method
from koldapi.configs import Config
from koldapi.requests import Request
from koldapi.responses import Response
from koldapi.routing import Route


class TestRoute:
    def setup_method(self):
        self.config = Config()
        self.receive = AsyncMock()
        self.send = AsyncMock()
        self.scope = {"type": "http", "path": "/test"}
        self.request = Request(self.scope, self.receive)

    def test_matches_raises_not_implemented_error(self):
        async def endpoint(_):
            return AsyncMock(spec=Response)

        route = Route("/test", endpoint, [Method.GET])

        with pytest.raises(NotImplementedError):
            route.matches(self.scope)

    @pytest.mark.asyncio
    async def test_call_with_async_endpoint(self):
        response = AsyncMock()

        async def endpoint(_):
            return response

        route = Route("/test", endpoint, [Method.GET])

        await route(self.config, self.scope, self.receive, self.send)

        response.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_call_with_sync_endpoint(self):
        response = AsyncMock(spec=Response)

        def endpoint(_):
            return response

        route = Route("/test", endpoint, [Method.GET])

        await route(self.config, self.scope, self.receive, self.send)

        response.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_raises_exception(self):
        async def endpoint(_):
            raise ValueError()

        route = Route("/test", endpoint, [Method.GET])

        with pytest.raises(ValueError):
            await route(self.config, self.scope, self.receive, self.send)
