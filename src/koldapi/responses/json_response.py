import json

from .base import Response


class JSONResponse(Response):
    """
    HTTP response class that serializes Python objects to JSON.

    Attributes:
        media_type: The media type for the response, default is "application/json".

    Example:
        >>> response = JSONResponse({"key": "value"})
        >>> response.serialize_content()
        b'{"key": "value"}'
    """

    media_type = "application/json"

    def serialize_content(self) -> bytes | memoryview:
        """
        Serialize the response content as a JSON-encoded bytes.

        Serializes self.content to a JSON-formatted
        byte string suitable for the HTTP response body.

        Returns:
            bytes | memoryview: The JSON-encoded response body.
        """
        return json.dumps(self.content or {}, ensure_ascii=False).encode(encoding=self.charset)
