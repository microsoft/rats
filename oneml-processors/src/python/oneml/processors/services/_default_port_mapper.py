from typing import Any, TypeVar

from oneml.io import IReadAndWriteData, IReadData, IWriteData

DataType = TypeVar("DataType")
DataType_co = TypeVar("DataType_co", covariant=True)
DataType_contra = TypeVar("DataType_contra", contravariant=True)


class DefaultTypeLocalRWMapper:
    _rw_mapper: dict[type, IReadAndWriteData[Any]]

    def __init__(self) -> None:
        self._rw_mapper = {}

    def get_rw(self, data_type: type[DataType]) -> IReadAndWriteData[DataType]:
        return self._rw_mapper[data_type]

    def get_reader(self, data_type: type[DataType_co]) -> IReadData[DataType_co]:
        return self._rw_mapper[data_type]

    def get_writer(self, data_type: type[DataType_contra]) -> IWriteData[DataType_contra]:
        return self._rw_mapper[data_type]

    def register(self, data_type: type[DataType], rw: IReadAndWriteData[DataType]) -> None:
        self._rw_mapper[data_type] = rw
