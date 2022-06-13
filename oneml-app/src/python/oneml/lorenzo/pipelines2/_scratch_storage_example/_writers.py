import dataclasses
import json
from abc import abstractmethod
from pathlib import Path
from typing import Any, Dict, Generic, List, Type, TypeVar

from oneml.lorenzo.pipelines import PipelineStorage
from oneml.lorenzo.pipelines._pipeline_storage import DataType

WriterType = TypeVar("WriterType")


class TypeWriter(Generic[WriterType]):
    @abstractmethod
    def write(self, data: WriterType) -> None:
        pass


class WriterRegistry:

    _writers: Dict[Type[WriterType], WriterType]

    def __init__(self):
        self._writers = {}

    def register(self, key: Type[WriterType], value: TypeWriter[WriterType]) -> None:
        self._writers[key] = value

    def get_writer(self, key: Type[WriterType]) -> TypeWriter[WriterType]:
        return self._writers[key]


class DictionaryWriter(TypeWriter[Dict[Any, Any]]):
    _path: Path

    def __init__(self, path: Path):
        self._path = path

    def write(self, data: Dict[Any, Any]) -> None:
        data = json.dumps(data, indent=2)
        directory = self._path.parent
        directory.mkdir(parents=True, exist_ok=True)
        self._path.unlink(missing_ok=True)
        self._path.write_text(data)


class BlobDictionaryWriter(TypeWriter[Dict[Any, Any]]):
    _path: Path

    def __init__(self, path: Path):
        self._path = path

    def write(self, data: Dict[Any, Any]) -> None:
        data = json.dumps(data, indent=2)
        self._blob_client.write(data, path)


class ListWriter(TypeWriter[List[Any]]):
    _path: Path

    def __init__(self, path: Path):
        self._path = path

    def write(self, data: List[Any]) -> None:
        data = json.dumps(data)
        self._path.unlink(missing_ok=True)
        self._path.write_text(data)

#
# class SamplesWriter(TypeWriter[Samples]):
#     _dict_writer: DictionaryWriter
#     _list_writer: ListWriter
#
#     def __init__(self, dict_writer: DictionaryWriter, list_writer: ListWriter):
#         self._dict_writer = dict_writer
#         self._list_writer = list_writer
#
#     def write(self, data: Samples) -> None:
#         self._dict_writer.write(data.data)
#         self._list_writer.write([data.foo_column, data.bar_column])


class DynamicWriter(TypeWriter, Generic[WriterType]):
    _registry: WriterRegistry
    _mapping: Dict[str, Type[WriterType]]

    def __init__(self, registry: WriterRegistry, mapping: Dict[str, Type[WriterType]]):
        self._registry = registry
        self._mapping = mapping

    def write(self, data: WriterType) -> None:
        for k, writer_type in self._mapping.items():
            value = getattr(data, k)
            self._registry.get_writer(writer_type).write(value)


class SimpleDataclassWriter(TypeWriter, Generic[WriterType]):
    _dict_writer: DictionaryWriter

    def __init__(self, dict_writer: DictionaryWriter):
        self._dict_writer = dict_writer

    def write(self, data: WriterType) -> None:
        if not dataclasses.is_dataclass(data):
            raise RuntimeError("NOT A DATA CLASS!")

        self._dict_writer.write(dataclasses.asdict(data))


class DataclassWriter(TypeWriter, Generic[WriterType]):
    _registry: WriterRegistry

    def __init__(self, registry: WriterRegistry):
        self._registry = registry

    def write(self, data: WriterType) -> None:
        if not dataclasses.is_dataclass(data):
            raise RuntimeError("NOT A DATA CLASS!")

        values = dataclasses.asdict(data)
        for prop, val in values.items():
            print(f"writing {prop}: {val}")
            writer = self._registry.get_writer(type(val))
            writer.write(val)


class LocalStorage(PipelineStorage):

    _writer_registry: WriterRegistry

    def __init__(self, writer_registry: WriterRegistry):
        self._writer_registry = writer_registry

    def save(self, key: Type[DataType], value: DataType) -> None:
        self._writer_registry.get_writer(key).write(value)

    def load(self, key: Type[DataType]) -> DataType:
        raise RuntimeError("AH")


class LocalStorage2(PipelineStorage):

    _writer_registry: WriterRegistry

    def __init__(self, writer_registry: WriterRegistry):
        self._writer_registry = writer_registry

    def save(self, key: Type[DataType], value: DataType) -> None:
        self._writer_registry.get_writer(key).write(value)

    def load(self, key: Type[DataType]) -> DataType:
        raise RuntimeError("AH")


def _run():
    registry = WriterRegistry()

    dict_writer = DictionaryWriter(path=Path("./dict-data.json"))
    list_writer = ListWriter(path=Path("./list-data.json"))
    simple_dataclass_writer = SimpleDataclassWriter(dict_writer=dict_writer)
    complex_dataclass_writer = DataclassWriter(registry=registry)
    # samples_writer = SamplesWriter(dict_writer=dict_writer, list_writer=list_writer)

    registry.register(Dict[Any, Any], dict_writer)
    registry.register(dict, dict_writer)
    registry.register(List[Any], list_writer)
    registry.register(str, list_writer)

    # registry.register(Samples, samples_writer)
    # registry.register(Samples, DynamicWriter[Samples](registry, {
    #     "data": Dict[Any, Any],
    #     "columns": List[Any],
    # }))
    # registry.register(Samples, simple_dataclass_writer)
    # registry.register(Samples, complex_dataclass_writer)

    storage = LocalStorage(writer_registry=registry)
    storage.save(Dict[Any, Any], dict(foo=5, bar=10))

    # samples = Samples(
    #     data=dict(foo234=123, bar678="bar"), foo_column="foo234", bar_column="bar678")
    #
    # storage.save(Samples, samples)


if __name__ == "__main__":
    _run()
