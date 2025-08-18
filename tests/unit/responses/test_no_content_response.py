import pytest

from koldapi.datastructures import Status
from koldapi.responses import NoContentResponse


class TestNoContentResponse:
    def test_content_is_always_none(self):
        resp = NoContentResponse()

        assert resp.content is None

    @pytest.mark.parametrize(
        "status_code",
        [
            Status.HTTP_100_CONTINUE,
            Status.HTTP_101_SWITCHING_PROTOCOLS,
            Status.HTTP_102_PROCESSING,
            Status.HTTP_103_EARLY_HINTS,
            Status.HTTP_204_NO_CONTENT,
            Status.HTTP_304_NOT_MODIFIED,
        ],
    )
    def test_allowed_status_codes_do_not_raise(self, status_code):
        resp = NoContentResponse(status_code=status_code)

        assert resp.status_code == status_code

    def test_media_type_is_none(self):
        resp = NoContentResponse()

        assert resp.media_type is None
