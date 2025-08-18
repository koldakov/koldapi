from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """
    Configuration settings for the application.

    Attributes:
        debug: Indicates whether the application is running in a debug mode.
            Defaults to False.
    """

    debug: bool = False
