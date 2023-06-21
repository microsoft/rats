import pickle
from typing import Any, TypeVar

from ._rw_data import IReadAndWriteData, RWDataUri

DataType = TypeVar("DataType")


class InMemoryRW(IReadAndWriteData[Any]):
    _data: dict[str, Any]

    def __init__(self) -> None:
        self._data = {}

    def write(self, data_uri: RWDataUri, payload: Any) -> None:
        self._data[data_uri.uri] = payload

    def read(self, data_uri: RWDataUri) -> Any:
        return self._data[data_uri.uri]


class PickleLocalRW(IReadAndWriteData[object]):
    def write(self, data_uri: RWDataUri, payload: object) -> None:
        with open(data_uri.uri, "wb") as f:
            pickle.dump(payload, f)

    def read(self, data_uri: RWDataUri) -> object:
        with open(data_uri.uri, "rb") as f:
            return pickle.load(f)
