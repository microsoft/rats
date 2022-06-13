from abc import ABC, abstractmethod
from typing import Any, Generic, Type, TypeVar

DataType = TypeVar("DataType")


class PipelineDataReader(ABC):
    @abstractmethod
    def load(self, key: Type[DataType]) -> DataType:
        pass


class PipelineDataWriter(ABC):
    @abstractmethod
    def save(self, key: Type[DataType], value: DataType) -> None:
        pass


class PipelineStorage(PipelineDataReader, PipelineDataWriter, ABC):
    pass


class NamespacePipelineDataReader(ABC, Generic[DataType]):
    @abstractmethod
    def load(self, key: str) -> DataType:
        pass


class NamespacePipelineDataWriter(ABC, Generic[DataType]):
    @abstractmethod
    def save(self, key: str, value: DataType) -> None:
        pass


class NamespacePipelineStorage(NamespacePipelineDataReader, NamespacePipelineDataWriter, ABC):
    pass


class DuplicateStorageKeyError(Exception):
    _key: Any

    def __init__(self, key: Any):
        self._key = key
        super().__init__(f"Duplicate storage key detected: {key}")


class StorageKeyNotFoundError(Exception):
    _key: Any

    def __init__(self, key: Any):
        self._key = key
        super().__init__(f"Storage key not found: {key}")
