import pytest

from koldapi.datastructures import Headers


class TestHeadersInit:
    def test_init_should_store_headers_case_insensitively(self):
        headers = Headers({"Content-Type": "application/json"})

        assert headers["content-type"] == "application/json"
        assert headers["Content-Type"] == "application/json"
        assert "content-type" in headers
        assert "Content-Type" in headers


class TestHeadersMagicMethods:
    def test_setitem_should_overwrite_existing_header_case_insensitively(self):
        headers = Headers({"Content-Type": "application/json"})
        headers["content-type"] = "text/html"

        assert headers["Content-Type"] == "text/html"

    def test_getitem_should_raise_key_error_when_key_is_missing(self):
        headers = Headers()

        with pytest.raises(KeyError):
            _ = headers["missing"]

    def test_delitem_should_remove_header_case_insensitively(self):
        headers = Headers({"Content-Type": "application/json"})

        del headers["Content-Type"]
        assert "content-type" not in headers

    def test_contains_should_return_false_for_non_str_key(self):
        headers = Headers({"Content-Type": "application/json"})

        assert 123 not in headers

    def test_len_should_return_number_of_headers(self):
        headers = Headers({"A": "1", "B": "2"})

        assert len(headers) == 2

    def test_iter_should_iterate_over_lowercased_keys(self):
        headers = Headers({"A": "1", "B": "2"})
        keys = list(iter(headers))

        assert keys == ["a", "b"]


class TestHeadersRaw:
    def test_raw_should_return_list_of_encoded_pairs(self):
        headers = Headers({"A": "1"})
        raw = headers.raw

        assert raw == [(b"a", b"1")]

    def test_raw_should_return_cache_if_cache_calculated(self):
        headers = Headers({"A": "1"})
        raw = headers.raw
        headers._store["b"] = "2"
        cached_raw = headers.raw
        headers["b"] = "2"
        recalculated_raw = headers.raw

        assert raw == [(b"a", b"1")]
        assert raw == cached_raw
        assert recalculated_raw == [(b"a", b"1"), (b"b", b"2")]


class TestHeadersFromScope:
    def test_from_scope_should_create_headers_instance(self):
        scope = {"headers": [(b"content-type", b"application/json"), (b"host", b"futuramaapi.com")]}
        headers = Headers.from_scope(scope)

        assert headers["Content-Type"] == "application/json"
        assert headers["Host"] == "futuramaapi.com"

    def test_from_scope_should_create_empty_headers_when_no_headers_present(self):
        scope = {"headers": []}
        headers = Headers.from_scope(scope)

        assert len(headers) == 0
