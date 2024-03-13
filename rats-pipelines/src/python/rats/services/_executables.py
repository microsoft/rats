from abc import abstractmethod
from collections.abc import Callable
from typing import Protocol, TypeVar

from ._services import ServiceId


class IExecutable(Protocol):
    @abstractmethod
    def execute(self) -> None: ...


T_ExecutableType = TypeVar("T_ExecutableType", bound=IExecutable)


def before(executable_id: ServiceId[T_ExecutableType]) -> ServiceId[IExecutable]:
    return ServiceId[IExecutable](f"/before[{executable_id.name}]")


def after(executable_id: ServiceId[T_ExecutableType]) -> ServiceId[IExecutable]:
    return ServiceId[IExecutable](f"/after[{executable_id.name}]")


class NoOpExecutable(IExecutable):
    def execute(self) -> None: ...


class _CallableExecutable(IExecutable):
    _callback: Callable[[], None]

    def __init__(self, callback: Callable[[], None]):
        self._callback = callback

    def execute(self) -> None:
        self._callback()


def executable(fn: Callable[[], None]) -> IExecutable:
    return _CallableExecutable(fn)
