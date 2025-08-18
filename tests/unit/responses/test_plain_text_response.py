from koldapi.responses import PlainTextResponse


class TestPlainTextResponse:
    def test_content_type_includes_charset(self):
        resp = PlainTextResponse("hello")

        assert resp.headers["content-type"] == f"text/plain; charset={PlainTextResponse.charset}"

    def test_content_type_without_content(self):
        resp = PlainTextResponse()

        assert resp.headers["content-type"] == f"text/plain; charset={PlainTextResponse.charset}"
