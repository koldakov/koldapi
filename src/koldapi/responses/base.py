from typing import Any, ClassVar

from koldapi._types import Receive, Scope, Send
from koldapi.datastructures import Headers, Status


class BaseResponseError(Exception):
    """Base Response Error."""


class IncorrectResponseStatusCodeError(BaseResponseError):
    """Incorrect Response Status Code Error."""


class Response:
    """
    Base Response class for HTTP response.

    Attributes:
        media_type: Default response media type if not provided
            explicitly by a subclass or instance.
        charset (str): Character encoding used for the response body.
            Defaults to UTF-8.
    """

    media_type: str | None = None
    charset: ClassVar[str] = "utf-8"

    def __init__(
        self,
        content: Any | None = None,
        *,
        status_code: Status = Status.HTTP_200_OK,
        headers: Headers | None = None,
        media_type: str | None = None,
    ) -> None:
        self._content: Any | None = content
        self.status_code: Status = status_code
        self.media_type: str | None = self._get_media_type(media_type)

        self.validate_empty_response()

        self._body: bytes | memoryview | None = None

        self.headers: Headers = headers or Headers()
        self._populate_headers()

    def validate_empty_response(self) -> None:
        """
        Validate the response.

        Raises:
            IncorrectResponseStatusCodeError: If content set when status_code doesn't imply the body.
        """
        if Status.body_not_allowed(self.status_code) and self.content:
            raise IncorrectResponseStatusCodeError(f"Content is not allowed for status_code={self.status_code}")

    def _get_media_type(self, media_type: str | None, /) -> str | None:
        """
        Get media type.

        Args:
            media_type: Default media type to set.

        Returns:
            Default to the response media type if none is provided,
                or use the provided media type otherwise.
        """
        if media_type is None:
            return self.media_type
        return media_type.lower()

    @property
    def content(self) -> Any | None:
        return self._content

    @property
    def content_length_required(self) -> bool:
        """
        Check if content length is required for the given response.

        Returns:
            True if content length is required and False otherwise.
        """
        if not self.content:
            return False

        return not Status.body_not_allowed(self.status_code)

    @property
    def content_type_required(self) -> bool:
        """
        Check if content type is required for the given response.

        Returns:
            True if content type is required and False otherwise.
        """
        return not Status.body_not_allowed(self.status_code) and "content-type" not in self.headers

    @property
    def content_type(self) -> str | None:
        """
        Construct the full Content-Type header value for the response.

        Includes the media type and appends the charset parameter if required.

        Returns:
            The Content-Type header string, e.g. "text/plain; charset=utf-8".
        """
        content_type: str | None = self.media_type
        if content_type and self.charset_required:
            content_type += "; charset=" + self.charset
        return content_type

    @property
    def charset_required(self) -> bool:
        """
        Check if a charset parameter should be included in the Content-Type header.

        Returns:
            True if the media type is a text-based type (starts with "text/")
                and does not already specify a charset; False otherwise.
        """
        if not self.media_type:
            return False
        return self.media_type.startswith("text/") and "charset=" not in self.media_type

    def _populate_headers(self) -> None:
        """
        Populate headers with default values such as content-type/content-length if required.
        """
        content_type: str | None = self.content_type
        if content_type and self.content_type_required:
            self.headers["content-type"] = content_type

        if self.content_length_required:
            self.headers["content-length"] = str(len(self))

    def serialize_content(self) -> bytes | memoryview:
        """
        Serialize the response for the ASGI server.

        Returns:
            The response body as bytes or a memoryview.
                Returns empty bytes if no content is set.
        """
        if self.content is None:
            return b""
        if isinstance(self.content, bytes | memoryview):
            return self.content
        return self.content.encode(self.charset)

    def render(self) -> bytes | memoryview:
        """
        Render the response for the ASGI server.
        If the body already calculated then return cache.

        Returns:
            The response body as bytes or a memoryview.
                Returns empty bytes if no content is set.
        """
        if self._body is not None:
            return self._body

        self._body = self.serialize_content()
        return self._body

    def __len__(self) -> int:
        return len(self.render())

    async def __call__(self, scope: Scope, receive: Receive, send: Send, /) -> None:
        """
        Send the HTTP response start event with the configured data.

        Args:
            scope: The ASGI connection scope.
            receive: ASGI callable to receive events.
            send: ASGI callable to send events.
        """
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": self.headers.raw,
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": self.render(),
            }
        )
