from unittest.mock import AsyncMock

import pytest

from koldapi.datastructures import Headers, Method, QueryParams
from koldapi.requests import (
    HTTPConnection,
    UnsupportedHTTPConnectionMethodError,
    WrongHTTPConnectionTypeError,
)


class TestHTTPConnectionValidate:
    def setup_method(self):
        self.receive = AsyncMock(return_value={"type": "INVALID"})

    def test_init_should_raise_when_connection_type_not_allowed(self):
        scope = {"type": "lifespan", "app": object(), "method": "GET", "query_string": b"pk=1&pk=2&type=user"}

        with pytest.raises(WrongHTTPConnectionTypeError):
            HTTPConnection(scope, self.receive)


class TestHTTPConnectionHeaders:
    def setup_method(self):
        self.receive = AsyncMock()

    def test_headers_should_return_when_scope_contains_headers(self):
        scope = {
            "type": "http",
            "app": object(),
            "method": "GET",
            "headers": [(b"host", b"futuramaapi.com")],
            "query_string": b"pk=1&pk=2&type=user",
        }
        conn = HTTPConnection(scope, self.receive)
        headers = conn.headers

        assert isinstance(headers, Headers)
        assert headers.get("host") == "futuramaapi.com"


class TestHTTPConnectionPathParams:
    def setup_method(self):
        self.receive = AsyncMock(return_value={})

    def test_path_params_should_return_when_scope_contains_path_params(self):
        path_params = {"id": 123}
        scope = {
            "type": "http",
            "app": object(),
            "method": "GET",
            "path_params": path_params,
            "query_string": b"pk=1&pk=2&type=user",
        }
        conn = HTTPConnection(scope, self.receive)

        assert conn.path_params == path_params

    def test_path_params_should_return_when_scope_does_not_contain_path_params(self):
        scope = {"type": "http", "app": object(), "method": "GET", "query_string": b"pk=1&pk=2&type=user"}
        conn = HTTPConnection(scope, self.receive)

        assert conn.path_params == {}


class TestHTTPConnectionQueryParams:
    def setup_method(self):
        self.receive = AsyncMock(return_value={})

    def test_query_params_should_return_query_params(self):
        scope = {
            "type": "http",
            "app": object(),
            "method": "GET",
            "query_string": "pk=1&pk=2&type=user".encode(QueryParams._encoding),
        }
        conn = HTTPConnection(scope, self.receive)

        assert isinstance(conn.query_params, QueryParams)
        assert conn.query_params["pk"] == ["1", "2"]
        assert conn.query_params["type"] == ["user"]


class TestHTTPConnectionApp:
    def setup_method(self):
        self.receive = AsyncMock(return_value={})

    def test_app_should_return_when_scope_contains_app(self):
        app = object()
        scope = {"type": "http", "app": app, "method": "GET", "query_string": b"pk=1&pk=2&type=user"}
        conn = HTTPConnection(scope, self.receive)

        assert conn.app is app


class TestHTTPConnectionMethod:
    def setup_method(self):
        self.receive = AsyncMock()

    def test_method_should_return_when_scope_contains_valid_http_method(self):
        scope = {"type": "http", "app": object(), "method": "POST", "query_string": b"pk=1&pk=2&type=user"}
        conn = HTTPConnection(scope, self.receive)

        assert conn.method == Method.POST

    def test_method_should_raise_when_scope_contains_invalid_http_method(self):
        scope = {"type": "http", "app": object(), "method": "INVALID", "query_string": b"pk=1&pk=2&type=user"}
        conn = HTTPConnection(scope, self.receive)

        with pytest.raises(UnsupportedHTTPConnectionMethodError):
            _ = conn.method


class TestHTTPConnectionScope:
    def setup_method(self):
        self.receive = AsyncMock()

    def test_scope_should_return_when_accessed(self):
        scope = {"type": "http", "app": object(), "method": "GET", "query_string": b"pk=1&pk=2&type=user"}
        conn = HTTPConnection(scope, self.receive)

        assert conn.scope == scope


class TestHTTPConnectionReceive:
    def setup_method(self):
        self.receive = AsyncMock()

    def test_receive_should_return_when_called(self):
        scope = {"type": "http", "app": object(), "method": "GET", "query_string": b"pk=1&pk=2&type=user"}
        conn = HTTPConnection(scope, self.receive)

        assert callable(conn.receive())


class TestHTTPConnectionMagicMethods:
    def setup_method(self):
        self.receive = AsyncMock()

    def test_getitem_should_return_when_key_in_scope(self):
        scope = {"type": "http", "app": object(), "method": "GET", "query_string": b"pk=1&pk=2&type=user"}
        conn = HTTPConnection(scope, self.receive)

        assert conn["method"] == Method.GET

    def test_iter_should_return_when_scope_contains_keys(self):
        scope = {"type": "http", "app": object(), "method": "GET", "query_string": b"pk=1&pk=2&type=user"}
        conn = HTTPConnection(scope, self.receive)
        keys = list(iter(conn))

        assert "method" in keys
        assert "type" in keys
        assert "app" in keys

    def test_len_should_return_when_scope_has_items(self):
        scope = {"type": "http", "app": object(), "method": "GET", "query_string": b"pk=1&pk=2&type=user"}
        conn = HTTPConnection(scope, self.receive)

        assert len(conn) == len(scope)
