from oneml.io import OnemlIoServices
from oneml.processors.io import (
    IRegisterReadServiceForType,
    IRegisterWriteServiceForType,
    PluginRegisterReadersAndWriters,
)


class OnemlProcessorsRegisterReadersAndWriters(PluginRegisterReadersAndWriters):
    def __init__(
        self,
        readers_registry: IRegisterReadServiceForType,
        writers_registry: IRegisterWriteServiceForType,
    ) -> None:
        super().__init__(readers_registry, writers_registry, [])

    def _register(self) -> None:
        self._readers_registry.register("memory", lambda t: True, OnemlIoServices.INMEMORY_READER)
        self._readers_registry.register("file", lambda t: True, OnemlIoServices.DILL_LOCAL_READER)
        self._writers_registry.register("memory", lambda t: True, OnemlIoServices.INMEMORY_WRITER)
        self._writers_registry.register("file", lambda t: True, OnemlIoServices.DILL_LOCAL_WRITER)
