from typing import Mapping, Sequence, TypeAlias, Union

from oneml.io import OnemlIoServices

from ._plugin_register_rw import PluginRegisterReadersAndWriters
from .type_rw_mappers import IRegisterReadServiceForType, IRegisterWriteServiceForType

JsonFormattable: TypeAlias = Union[
    Mapping[str, "JsonFormattable"],
    str,
    int,
    float,
    Sequence["JsonFormattable"],
]


class Manifest(dict[str, JsonFormattable]):
    ...


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
        self._register_manifest()

    def _register_manifest(self) -> None:
        def type_filter(t: type) -> bool:
            if not isinstance(t, type):
                return False
            return issubclass(t, Manifest)

        self._readers_registry.register("file", type_filter, OnemlIoServices.JSON_LOCAL_READER)
        self._writers_registry.register("file", type_filter, OnemlIoServices.JSON_LOCAL_WRITER)
