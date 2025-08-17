import pytest

from koldapi.datastructures import State


class TestStateMagicMethods:
    def setup_method(self):
        self.state = State()

    def test_getattr_should_return_value_when_key_exists(self):
        self.state["foo"] = "bar"

        assert self.state.foo == "bar"

    def test_getattr_should_raise_attribute_error_when_key_does_not_exist(self):
        with pytest.raises(AttributeError) as exc:
            _ = self.state.nonexistent

        assert 'object has no attribute "nonexistent"' in str(exc.value)

    def test_setattr_should_set_value_when_attribute_is_assigned(self):
        self.state.foo = "baz"

        assert self.state["foo"] == "baz"

    def test_delattr_should_remove_key_when_attribute_is_deleted(self):
        self.state["foo"] = "to be deleted"
        del self.state.foo

        assert "foo" not in self.state

    def test_delattr_should_raise_key_error_when_key_does_not_exist(self):
        with pytest.raises(KeyError):
            del self.state.foo
