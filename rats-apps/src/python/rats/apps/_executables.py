from abc import abstractmethod
from collections.abc import Callable
from typing import Protocol


class Executable(Protocol):
    @abstractmethod
    def execute(self) -> None: ...


class App(Executable):
    _callback: Callable[[], None]

    def __init__(self, callback: Callable[[], None]) -> None:
        self._callback = callback

    def execute(self) -> None:
        self._callback()
