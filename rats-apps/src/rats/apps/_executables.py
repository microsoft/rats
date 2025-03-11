from abc import abstractmethod
from collections.abc import Callable
from typing import Protocol


class Executable(Protocol):
    """
    An interface for an executable object.

    One of the lowest level abstractions in the rats-apps library, executables are meant to be
    easy to run from anywhere, with limited knowledge of the implementation details of the object,
    by ensuring that the object has an `execute` method with no arguments.
    """

    @abstractmethod
    def execute(self) -> None:
        """Execute the application."""


class App(Executable):
    """
    Wraps a plain callable objects as a [rats.apps.Executable][].

    This simple object allows for turning any callable object into an executable that is recognized
    by the rest of the rats application.

    Example:
        ```python
        from rats import apps

        apps.App(lambda: print("hello, world")).execute()
        ```
    """

    _callback: Callable[[], None]

    def __init__(self, callback: Callable[[], None]) -> None:
        """
        Created by providing a reference to a `Callable[[], None]` function.

        Args:
            callback: called when the application instance is executed.
        """
        self._callback = callback

    def execute(self) -> None:
        """Runs the provided callback."""
        self._callback()
