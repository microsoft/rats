from abc import abstractmethod
from typing import Callable, Protocol


class App(Protocol):
    @abstractmethod
    def run(self, callback: Callable[[], None]) -> None:
        pass
