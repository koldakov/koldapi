from dataclasses import FrozenInstanceError

import pytest

from koldapi import Config


class TestAppConfig:
    def test_default_debug_is_false(self):
        config = Config()

        assert config.debug is False

    def test_can_set_debug_true(self):
        config = Config(debug=True)
        assert config.debug is True

    def test_mutability_is_frozen(self):
        config = Config()

        with pytest.raises(FrozenInstanceError):
            config.debug = True  # type: ignore[misc]
