from typing import Any


class State(dict[str, Any]):
    """
    A state container for ASGI applications with both dict and attribute access.

    Commonly used to store application-wide resources such as database
    connections, configuration, or external service clients.
    """

    def __getattr__(self, key: str) -> Any:
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f'"{self.__class__.__name__}" object has no attribute "{key}"') from None

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value

    def __delattr__(self, key: str) -> None:
        del self[key]
