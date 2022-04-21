from abc import ABC, abstractmethod
from typing import Type, TypeVar

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


class DuplicateStorageKeyError(Exception):
    _key: Type[DataType]

    def __init__(self, key: Type[DataType]):
        self._key = key
        super().__init__(f"Duplicate storage key detected: {key}")


class StorageKeyNotFoundError(Exception):
    _key: Type[DataType]

    def __init__(self, key: Type[DataType]):
        self._key = key
        super().__init__(f"Storage key not found: {key}")
