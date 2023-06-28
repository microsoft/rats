import pickle
from pathlib import Path
from typing import Any, TypeVar

from furl import furl

from ._rw_data import IReadAndWriteData, RWDataUri

DataType = TypeVar("DataType")


class InMemoryRW(IReadAndWriteData[Any]):
    _data: dict[str, Any]

    def __init__(self) -> None:
        self._data = {}

    def _get_key(self, data_uri: RWDataUri) -> str:
        split_uri = furl(data_uri.uri)
        if split_uri.scheme != "memory":
            raise ValueError(f"Expected memory scheme, got {split_uri.scheme}")
        if split_uri.netloc:
            raise ValueError(f"Expected empty netloc, got {split_uri.netloc}")
        if not split_uri.path:
            raise ValueError(f"Expected non-empty path, got {split_uri.path}")
        if split_uri.query:
            raise ValueError(f"Expected empty query, got {split_uri.query}")
        if split_uri.fragment:
            raise ValueError(f"Expected empty fragment, got {split_uri.fragment}")
        return str(split_uri.path)

    def write(self, data_uri: RWDataUri, payload: Any) -> None:
        key = self._get_key(data_uri)
        self._data[key] = payload

    def read(self, data_uri: RWDataUri) -> Any:
        key = self._get_key(data_uri)
        return self._data[key]


class LocalRWBase:
    def _get_path(self, data_uri: RWDataUri) -> Path:
        split_uri = furl(data_uri.uri)
        if split_uri.scheme != "file":
            raise ValueError(f"Expected file scheme, got {split_uri.scheme}")
        if split_uri.netloc:
            raise ValueError(f"Expected empty netloc, got {split_uri.netloc}")
        if not split_uri.path:
            raise ValueError(f"Expected non-empty path, got {split_uri.path}")
        if split_uri.query:
            raise ValueError(f"Expected empty query, got {split_uri.query}")
        if split_uri.fragment:
            raise ValueError(f"Expected empty fragment, got {split_uri.fragment}")
        return Path(str(split_uri.path))


class PickleLocalRW(LocalRWBase, IReadAndWriteData[object]):
    def write(self, data_uri: RWDataUri, payload: object) -> None:
        path = self._get_path(data_uri)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as f:
            pickle.dump(payload, f)

    def read(self, data_uri: RWDataUri) -> object:
        path = self._get_path(data_uri)
        with path.open("rb") as f:
            return pickle.load(f)
