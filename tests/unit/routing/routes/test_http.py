from unittest.mock import AsyncMock

import pytest

from koldapi import Method
from koldapi.configs import Config
from koldapi.requests import Request
from koldapi.responses import Response
from koldapi.routing import Route
from koldapi.routing.routes import InvalidPathParamsError, InvalidRequestTypeError, Match


class TestRoute:
    def setup_method(self):
        self.config = Config()
        self.receive = AsyncMock()
        self.send = AsyncMock()
        self.scope = {"type": "http", "path": "/test", "method": "get"}
        self.scope_with_path_params = {
            "type": "http",
            "path": "/users/1",
            "method": "get",
            "path_params": {"user_id": "1"},
        }
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

        async def endpoint():
            return response

        route = Route("/test", endpoint, [Method.GET])

        await route(self.config, self.scope, self.receive, self.send)

        response.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_call_with_sync_endpoint(self):
        response = AsyncMock(spec=Response)

        def endpoint():
            return response

        route = Route("/test", endpoint, [Method.GET])

        await route(self.config, self.scope, self.receive, self.send)

        response.assert_called_once()

    @pytest.mark.asyncio
    async def test_call_raises_exception(self):
        async def endpoint():
            raise ValueError()

        route = Route("/test", endpoint, [Method.GET])

        with pytest.raises(ValueError):
            await route(self.config, self.scope, self.receive, self.send)

    @pytest.mark.asyncio
    async def test_call_args_when_request_not_provided(self):
        service = AsyncMock()

        async def endpoint():
            await service()
            return AsyncMock(spec=Response)

        route = Route("/test", endpoint, [Method.GET])
        await route(self.config, self.scope, self.receive, self.send)

        await service.awaited_once()

    @pytest.mark.asyncio
    async def test_call_args_when_request_type_not_provided(self):
        service = AsyncMock()

        async def endpoint(request):
            await service()
            return AsyncMock(spec=Response)

        route = Route("/test", endpoint, [Method.GET])
        await route(self.config, self.scope, self.receive, self.send)

        await service.awaited_once()

    @pytest.mark.asyncio
    async def test_call_args_when_request_type_provided_and_correct(self):
        service = AsyncMock()

        async def endpoint(request: Request):
            await service()
            return AsyncMock(spec=Response)

        route = Route("/test", endpoint, [Method.GET])
        await route(self.config, self.scope, self.receive, self.send)

        await service.awaited_once()

    @pytest.mark.asyncio
    async def test_call_args_when_request_type_provided_and_incorrect(self):
        service = AsyncMock()

        async def endpoint(request: int):
            await service()
            return AsyncMock(spec=Response)

        route = Route("/test", endpoint, [Method.GET])

        with pytest.raises(InvalidRequestTypeError):
            await route(self.config, self.scope, self.receive, self.send)

    @pytest.mark.asyncio
    async def test_call_args_with_path_params_without_type(self):
        async def endpoint(user_id):
            assert isinstance(user_id, str)
            return AsyncMock(spec=Response)

        route = Route("/users/{user_id}", endpoint, [Method.GET])
        await route(self.config, self.scope_with_path_params, self.receive, self.send)

    @pytest.mark.asyncio
    async def test_call_args_with_path_params_with_type(self):
        async def endpoint(user_id: int):
            assert isinstance(user_id, int)
            return AsyncMock(spec=Response)

        route = Route("/users/{user_id}", endpoint, [Method.GET])
        await route(self.config, self.scope_with_path_params, self.receive, self.send)

    @pytest.mark.asyncio
    async def test_call_args_with_path_params_with_wrong_type(self):
        scope = self.scope_with_path_params.copy()
        scope["path"] = "/users/user_id"
        scope["path_params"] = {"user_id": "user_id"}

        async def endpoint(user_id: int):
            return AsyncMock(spec=Response)

        route = Route("/users/{user_id}", endpoint, [Method.GET])

        with pytest.raises(InvalidPathParamsError):
            await route(self.config, scope, self.receive, self.send)

    @pytest.mark.asyncio
    async def test_call_args_with_path_params_when_path_params_provided_and_request_provided(self):
        scope = self.scope_with_path_params.copy()
        scope["path"] = "/users/2/user_action"
        scope["path_params"] = {"user_id": "1", "user_action": "user_action"}

        async def endpoint(request: Request, user_id: int, user_action):
            assert isinstance(request, Request)
            assert isinstance(user_id, int)
            return AsyncMock(spec=Response)

        route = Route("/users/{user_id}/{user_action}", endpoint, [Method.GET])

        await route(self.config, scope, self.receive, self.send)
