from abc import abstractmethod
from collections.abc import Callable, Iterator
from functools import cache
from typing import Protocol

from ._container import Container, ServiceId
from ._ids import T_ServiceType


class Executable(Protocol):
    @abstractmethod
    def execute(self) -> None:
        """Execute the application."""


class App(Executable):
    _callback: Callable[[], None]

    def __init__(self, callback: Callable[[], None]) -> None:
        self._callback = callback

    def execute(self) -> None:
        self._callback()


class AppContainer(Container):
    _container: Callable[[Container], Container]

    def __init__(self, container: Callable[[Container], Container]) -> None:
        self._container = container

    def get_namespaced_group(
        self,
        namespace: str,
        group_id: ServiceId[T_ServiceType],
    ) -> Iterator[T_ServiceType]:
        yield from self._load_container().get_namespaced_group(namespace, group_id)

    @cache  # noqa: B019
    def _load_container(self) -> Container:
        return self._container(self)
