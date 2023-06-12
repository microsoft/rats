from abc import abstractmethod
from typing import Any, Dict, Generic, Protocol, TypeVar

from typing_extensions import NamedTuple

DataType = TypeVar("DataType")


class IoDataId(NamedTuple, Generic[DataType]):
    uri: str


class IDataWriter(Protocol):

    @abstractmethod
    def write(self, data_id: IoDataId[DataType], payload: DataType) -> None:
        pass


class IDataReader(Protocol):

    @abstractmethod
    def read(self, data_id: IoDataId[DataType]) -> DataType:
        pass


class IDataManager(IDataWriter, IDataReader, Protocol):
    pass


class IoDataMapper(IDataManager):
    # TODO: let's flesh out how the pipeline data layer interacts with this one.

    _data: Dict[IoDataId[Any], Any]

    def __init__(self) -> None:
        self._data = {}

    def write(self, data_id: IoDataId[DataType], payload: DataType) -> None:
        self._data[data_id] = payload

    def read(self, data_id: IoDataId[DataType]) -> DataType:
        return self._data[data_id]
