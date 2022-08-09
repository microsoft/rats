from abc import abstractmethod
from typing import Protocol


class IExecutable(Protocol):
    @abstractmethod
    def execute(self) -> None:
        """

        """


class ICallableExecutableProvider(Protocol):
    @abstractmethod
    def __call__(self) -> IExecutable:
        pass


class DeferredExecutable(IExecutable):
    _callback: ICallableExecutableProvider

    def __init__(self, callback: ICallableExecutableProvider):
        self._callback = callback

    def execute(self) -> None:
        self._callback().execute()
