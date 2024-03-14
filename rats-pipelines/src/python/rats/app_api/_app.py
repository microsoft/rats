from abc import abstractmethod
from collections.abc import Callable
from typing import Protocol


class App(Protocol):
    @abstractmethod
    def run(self, callback: Callable[[], None]) -> None:
        pass
