from unittest.mock import AsyncMock

import pytest

from koldapi import Method
from koldapi.configs import Config
from koldapi.requests import Request
from koldapi.responses import Response
from koldapi.routing import Route
from koldapi.routing.routes import Match


class TestRoute:
    def setup_method(self):
        self.config = Config()
        self.receive = AsyncMock()
        self.send = AsyncMock()
        self.scope = {"type": "http", "path": "/test", "method": "get"}
        self.request = Request(self.scope, self.receive)

    def test_matches_returns_full_match_when_path_contains_parameters(self):
        async def endpoint(_):
            return AsyncMock(spec=Response)

        param_name = "test_name"
        second_param_name = "second_test_name"

        scope = self.scope.copy()
        scope["path"] = f"/test/{param_name}/{second_param_name}"

        route = Route("/test/{name}/{second_name}", endpoint, [Method.GET])
        match, route_scope = route.matches(scope)

        assert match == Match.FULL
        assert route_scope["path_params"] == {"name": param_name, "second_name": second_param_name}

    def test_matches_returns_full_match(self):
        async def endpoint(_):
            return AsyncMock(spec=Response)

        route = Route("/test", endpoint, [Method.GET])
        match, _ = route.matches(self.scope)

        assert match == Match.FULL

    def test_matches_returns_partial_match(self):
        async def endpoint(_):
            return AsyncMock(spec=Response)

        route = Route("/test", endpoint, [Method.POST])
        match, _ = route.matches(self.scope)

        assert match == Match.PARTIAL

    def test_matches_returns_none_match(self):
        async def endpoint(_):
            return AsyncMock(spec=Response)

        route = Route("/tests", endpoint, [Method.GET])
        match, _ = route.matches(self.scope)

        assert match == Match.NONE

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
