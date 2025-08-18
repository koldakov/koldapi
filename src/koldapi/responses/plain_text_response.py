from .base import Response


class PlainTextResponse(Response):
    """
    HTTP response for plain text content.

    This response type automatically sets the Content-Type to "text/plain"
    and appends the charset (UTF-8 by default) if required. The body can
    contain any text content, which will be encoded to bytes when rendered.

    Attributes:
        media_type: Always "text/plain".
    """

    media_type = "text/plain"
