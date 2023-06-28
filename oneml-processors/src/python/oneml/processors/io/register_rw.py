from oneml.io import OnemlIoServices

from .type_rw_mappers import IRegisterReadServiceForType, IRegisterWriteServiceForType


class OnemlProcessorsRegisterReadersAndWriters:
    _readers_registry: IRegisterReadServiceForType
    _writers_registry: IRegisterWriteServiceForType

    def __init__(
        self,
        readers_registry: IRegisterReadServiceForType,
        writers_registry: IRegisterWriteServiceForType,
    ) -> None:
        self._readers_registry = readers_registry
        self._writers_registry = writers_registry

    def register(self) -> None:
        self._readers_registry.register("memory", lambda t: True, OnemlIoServices.INMEMORY_READER)
        self._readers_registry.register(
            "file", lambda t: True, OnemlIoServices.PICKLE_LOCAL_READER
        )
        self._writers_registry.register("memory", lambda t: True, OnemlIoServices.INMEMORY_WRITER)
        self._writers_registry.register(
            "file", lambda t: True, OnemlIoServices.PICKLE_LOCAL_WRITER
        )
