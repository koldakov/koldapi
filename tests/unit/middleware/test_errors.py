from unittest.mock import AsyncMock

import pytest

from koldapi.configs import Config
from koldapi.middleware import ServerErrorMiddleware


class TestServerErrorMiddleware:
    def setup_method(self):
        async def failing_app(_scope, _receive, _send):
            raise ValueError("Boom!")

        self.failing_app = failing_app
        self.receive = AsyncMock()
        self.send = AsyncMock()
        self.scope = {"type": "http"}

    @pytest.mark.asyncio
    async def test_server_error_middleware_when_debug_is_true(self):
        config = Config(debug=True)
        middleware = ServerErrorMiddleware(self.failing_app, config)

        with pytest.raises(ValueError, match="Boom!"):
            await middleware(self.scope, self.receive, self.send)

        self.send.assert_awaited()

    @pytest.mark.asyncio
    async def test_server_error_middleware_when_debug_is_false(self):
        config = Config(debug=False)
        middleware = ServerErrorMiddleware(self.failing_app, config)

        with pytest.raises(ValueError, match="Boom!"):
            await middleware(self.scope, self.receive, self.send)

        self.send.assert_not_awaited()
