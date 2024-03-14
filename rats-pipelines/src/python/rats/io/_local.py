import json
import logging
from pathlib import Path
from typing import TypeVar

import dill
from furl import furl

from ._rw_data import IReadAndWriteData, RWDataUri

DataType = TypeVar("DataType")

logger = logging.getLogger(__name__)


class LocalRWBase:
    def _get_path(self, data_uri: RWDataUri) -> Path:
        split_uri = furl(data_uri.uri)
        if split_uri.scheme != "file":  # type: ignore[reportUnknownMemberType]
            raise ValueError(f"Expected file scheme, got {split_uri.scheme}")  # type: ignore[reportUnknownMemberType]
        if split_uri.netloc:  # type: ignore[reportUnknownMemberType]
            raise ValueError(f"Expected empty netloc, got {split_uri.netloc}")  # type: ignore[reportUnknownMemberType]
        if not split_uri.path:
            raise ValueError(f"Expected non-empty path, got {split_uri.path}")
        if split_uri.query:
            raise ValueError(f"Expected empty query, got {split_uri.query}")
        if split_uri.fragment:
            raise ValueError(f"Expected empty fragment, got {split_uri.fragment}")
        return Path(str(split_uri.path))


class DillLocalRW(LocalRWBase, IReadAndWriteData[object]):
    def write(self, data_uri: RWDataUri, payload: object) -> None:
        logger.debug(f"{self.__class__.__name__}: writing to {data_uri}")
        path = self._get_path(data_uri)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("wb") as f:
            dill.dump(payload, f)  # type: ignore[reportUnknownMemberType]

    def read(self, data_uri: RWDataUri) -> object:
        logger.debug(f"{self.__class__.__name__}: reading from {data_uri}")
        path = self._get_path(data_uri)
        with path.open("rb") as f:
            return dill.load(f)  # type: ignore[reportUnknownMemberType]


class JsonLocalRW(LocalRWBase, IReadAndWriteData[object]):
    def write(self, data_uri: RWDataUri, payload: object) -> None:
        logger.debug(f"{self.__class__.__name__}: writing to {data_uri}")
        path = self._get_path(data_uri)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as f:
            json.dump(payload, f)

    def read(self, data_uri: RWDataUri) -> object:
        logger.debug(f"{self.__class__.__name__}: reading from {data_uri}")
        path = self._get_path(data_uri)
        with path.open("r") as f:
            return json.load(f)
