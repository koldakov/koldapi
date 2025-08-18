import json

from koldapi.responses import JSONResponse


class TestJSONResponse:
    def test_serialize_content_should_return_json_bytes(self):
        data = {"key": "value"}
        resp = JSONResponse(data)
        result = resp.serialize_content()

        assert isinstance(result, bytes)
        assert json.loads(result) == data

    def test_serialize_content_should_return_empty_json_object_if_content_is_none(self):
        resp = JSONResponse(None)
        result = resp.serialize_content()

        assert isinstance(result, bytes)
        assert json.loads(result) == {}
