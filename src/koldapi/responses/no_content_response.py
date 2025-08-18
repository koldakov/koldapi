from __future__ import annotations

from typing import Literal

from koldapi.datastructures import Headers, Status

from .base import Response


class NoContentResponse(Response):
    """
    Specialized HTTP response for status codes that must not contain a body.

    This response type is immutable in terms of content (always None)
    and sets the default status code to 204 No Content. Other allowed
    status codes are those defined in HTTP that do not permit a body.

    Attributes:
        media_type: No content type is set because the response has no body.
    """

    media_type = None

    def __init__(
        self,
        *,
        status_code: Literal[
            Status.HTTP_100_CONTINUE,
            Status.HTTP_101_SWITCHING_PROTOCOLS,
            Status.HTTP_102_PROCESSING,
            Status.HTTP_103_EARLY_HINTS,
            Status.HTTP_204_NO_CONTENT,
            Status.HTTP_304_NOT_MODIFIED,
        ] = Status.HTTP_204_NO_CONTENT,
        headers: Headers | None = None,
    ) -> None:
        super().__init__(
            None,
            status_code=status_code,
            headers=headers,
            media_type=None,
        )
