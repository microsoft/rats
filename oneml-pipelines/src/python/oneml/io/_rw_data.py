from abc import abstractmethod
from typing import Protocol, TypeVar

from typing_extensions import NamedTuple

DataType = TypeVar("DataType")
DataType_co = TypeVar("DataType_co", covariant=True)
DataType_contra = TypeVar("DataType_contra", contravariant=True)


class RWDataUri(NamedTuple):
    uri: str


class IReadData(Protocol[DataType_co]):
    @abstractmethod
    def read(self, data_uri: RWDataUri) -> DataType_co:
        pass


class IWriteData(Protocol[DataType_contra]):
    @abstractmethod
    def write(self, data_uri: RWDataUri, payload: DataType_contra) -> None:
        pass


class IReadAndWriteData(IReadData[DataType], IWriteData[DataType]):
    pass
