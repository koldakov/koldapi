from enum import StrEnum


class Method(StrEnum):
    """Enumeration of standard HTTP methods as defined by various RFCs."""

    # RFC 7231
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    TRACE = "TRACE"
    # RFC 5789
    PATCH = "PATCH"
    # RFC 2616
    CONNECT = "CONNECT"
    # RFC 4918
    PROPFIND = "PROPFIND"
    PROPPATCH = "PROPPATCH"
    MKCOL = "MKCOL"
    COPY = "COPY"
    MOVE = "MOVE"
    LOCK = "LOCK"
    UNLOCK = "UNLOCK"
