from abc import abstractmethod
from typing import Callable, Protocol


class IExecutable(Protocol):
    @abstractmethod
    def execute(self) -> None:
        pass


class DeferredExecutable(IExecutable):
    _callback: Callable[[], IExecutable]

    def __init__(self, callback: Callable[[], IExecutable]):
        self._callback = callback

    def execute(self) -> None:
        self._callback().execute()
