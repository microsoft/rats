from __future__ import annotations

from abc import abstractmethod
from collections.abc import Iterable

from rats.services import IExecutable

from .type_rw_mappers import IRegisterReadServiceForType, IRegisterWriteServiceForType


class PluginRegisterReadersAndWriters(IExecutable):
    _readers_registry: IRegisterReadServiceForType
    _writers_registry: IRegisterWriteServiceForType
    _upstream_plugins: list[PluginRegisterReadersAndWriters]
    _done: bool

    def __init__(
        self,
        readers_registry: IRegisterReadServiceForType,
        writers_registry: IRegisterWriteServiceForType,
        upstream_plugins: Iterable[PluginRegisterReadersAndWriters],
    ) -> None:
        self._readers_registry = readers_registry
        self._writers_registry = writers_registry
        self._upstream_plugins = list(upstream_plugins)
        self._done = False

    @abstractmethod
    def _register(self) -> None: ...

    def execute(self) -> None:
        if not self._done:
            for plugin in self._upstream_plugins:
                plugin.execute()
            self._register()
            self._done = True
