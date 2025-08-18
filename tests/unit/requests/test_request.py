from unittest.mock import AsyncMock

import pytest

from koldapi.requests import Request, WrongHTTPBodyFormatError


class TestRequestBody:
    def setup_method(self):
        self.scope = {"type": "http", "app": object(), "method": "POST"}

    @pytest.mark.asyncio
    async def test_body_should_return_when_called_first_time(self):
        messages = [
            {"body": b"hello ", "more_body": True},
            {"body": b"world", "more_body": False},
        ]
        receive = AsyncMock(side_effect=messages)
        request = Request(self.scope, receive)
        body = await request.body()

        assert body == b"hello world"
        assert receive.call_count == 2

    @pytest.mark.asyncio
    async def test_body_should_return_cached_body_when_called_second_time(self):
        messages = [{"body": b"data", "more_body": False}]
        receive = AsyncMock(side_effect=messages)
        request = Request(self.scope, receive)
        body1 = await request.body()
        body2 = await request.body()

        assert body1 is body2
        receive.assert_awaited_once()


class TestRequestJSON:
    def setup_method(self):
        self.scope = {"type": "http", "app": object(), "method": "POST"}

    @pytest.mark.asyncio
    async def test_json_should_return_when_body_is_valid_json(self):
        messages = [{"body": b'{"key": "value"}', "more_body": False}]
        receive = AsyncMock(side_effect=messages)
        request = Request(self.scope, receive)
        data = await request.json()

        assert data == {"key": "value"}
        receive.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_json_should_return_cached_json_when_called_second_time(self):
        messages = [{"body": b'{"a": 1}', "more_body": False}]
        receive = AsyncMock(side_effect=messages)
        request = Request(self.scope, receive)
        body1 = await request.json()
        body2 = await request.json()

        assert body1 is body2
        receive.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_json_should_raise_when_body_is_invalid_json(self):
        messages = [{"body": b"not json", "more_body": False}]
        receive = AsyncMock(side_effect=messages)
        request = Request(self.scope, receive)

        with pytest.raises(WrongHTTPBodyFormatError):
            await request.json()
