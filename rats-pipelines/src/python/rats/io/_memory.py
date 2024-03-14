import logging
from typing import Any, TypeVar

from furl import furl

from ._rw_data import IReadAndWriteData, RWDataUri

DataType = TypeVar("DataType")

logger = logging.getLogger(__name__)


class InMemoryRW(IReadAndWriteData[Any]):
    _data: dict[str, Any]

    def __init__(self) -> None:
        self._data = {}

    def _get_key(self, data_uri: RWDataUri) -> str:
        split_uri = furl(data_uri.uri)
        if split_uri.scheme != "memory":  # type: ignore[reportUnknownMemberType]
            raise ValueError(f"Expected memory scheme, got {split_uri.scheme}")  # type: ignore[reportUnknownMemberType]
        if split_uri.netloc is not None and len(split_uri.netloc) > 0:  # type: ignore[reportUnknownMemberType]
            raise ValueError(f"Expected empty netloc, got {split_uri.netloc}")  # type: ignore[reportUnknownMemberType]
        if not split_uri.path:
            raise ValueError(f"Expected non-empty path, got {split_uri.path}")
        if split_uri.query:
            raise ValueError(f"Expected empty query, got {split_uri.query}")
        if split_uri.fragment:
            raise ValueError(f"Expected empty fragment, got {split_uri.fragment}")
        return str(split_uri.path)

    def write(self, data_uri: RWDataUri, payload: Any) -> None:
        logger.debug(f"{self.__class__.__name__}: writing to {data_uri}")
        key = self._get_key(data_uri)
        self._data[key] = payload

    def read(self, data_uri: RWDataUri) -> Any:
        logger.debug(f"{self.__class__.__name__}: reading from {data_uri}")
        key = self._get_key(data_uri)
        return self._data[key]
