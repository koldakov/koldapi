from unittest.mock import AsyncMock

import pytest

from koldapi.datastructures import Headers, Status
from koldapi.responses import IncorrectResponseStatusCodeError, Response


class TestResponseContent:
    def test_serialize_content_should_return_bytes_when_content_is_str(self):
        response = Response("hello")

        assert response.serialize_content() == b"hello"

    def test_serialize_content_should_return_bytes_when_content_is_bytes(self):
        response = Response(b"hello")

        assert response.serialize_content() == b"hello"

    def test_serialize_content_should_return_empty_bytes_when_content_is_none(self):
        response = Response(None)

        assert response.serialize_content() == b""

    def test_render_should_cache_body_on_second_call(self):
        response = Response("test")
        rendered_response1 = response.render()
        rendered_response2 = response.render()

        assert rendered_response1 is rendered_response2


class TestResponseHeaders:
    def test_headers_should_include_content_type_when_required(self):
        response = Response("hello", media_type="text/plain")

        assert response.headers["content-type"] == f"text/plain; charset={Response.charset}"

    def test_headers_should_include_content_length_when_required(self):
        response = Response("abc")

        assert response.headers["content-length"] == str(len(response))

    def test_content_type_required_should_return_false_if_content_type_already_set(self):
        headers = Headers({"content-type": "text/plain"})
        response = Response("abc", headers=headers, media_type="text/plain")

        assert not response.content_type_required

    def test_charset_required_should_return_true_for_text_media_type(self):
        response = Response("abc", media_type="text/plain")

        assert response.charset_required

    def test_charset_required_should_return_false_for_non_text_media_type(self):
        response = Response("abc", media_type="application/json")

        assert not response.charset_required

    def test_charset_required_should_return_false_if_no_media_type(self):
        response = Response("abc", media_type=None)

        assert not response.charset_required


class TestResponseValidation:
    def test_validate_empty_response_should_raise_if_body_not_allowed(self):
        with pytest.raises(IncorrectResponseStatusCodeError):
            Response("body not allowed", status_code=Status.HTTP_204_NO_CONTENT)


class TestResponseASGICall:
    @pytest.mark.asyncio
    async def test_call_should_send_response_events(self):
        response = Response("hello", media_type="text/plain")
        send = AsyncMock()

        await response({}, AsyncMock(), send)

        assert send.await_count == 2
        start_event, body_event = send.await_args_list[0][0][0], send.await_args_list[1][0][0]
        assert start_event["type"] == "http.response.start"
        assert start_event["status"] == response.status_code
        assert body_event["type"] == "http.response.body"
        assert body_event["body"] == b"hello"
