from abc import abstractmethod
from typing import Protocol, TypeVar

from typing_extensions import NamedTuple

T_DataType = TypeVar("T_DataType")
Tco_DataType = TypeVar("Tco_DataType", covariant=True)
Tcontra_DataType = TypeVar("Tcontra_DataType", contravariant=True)


class RWDataUri(NamedTuple):
    uri: str

    def __repr__(self) -> str:
        return self.uri


class IReadData(Protocol[Tco_DataType]):
    @abstractmethod
    def read(self, data_uri: RWDataUri) -> Tco_DataType:
        pass


class IWriteData(Protocol[Tcontra_DataType]):
    @abstractmethod
    def write(self, data_uri: RWDataUri, payload: Tcontra_DataType) -> None:
        pass


class IReadAndWriteData(IReadData[T_DataType], IWriteData[T_DataType], Protocol):
    pass
