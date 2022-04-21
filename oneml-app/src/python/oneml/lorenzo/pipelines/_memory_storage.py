from typing import Dict, Type, Any
import logging

from ._pipeline_storage import (
    PipelineStorage,
    DataType,
    DuplicateStorageKeyError,
    StorageKeyNotFoundError
)

logger = logging.getLogger(__name__)


class InMemoryStorage(PipelineStorage):

    _data: Dict[Type[Any], Any]

    def __init__(self):
        self._data = {}

    def save(self, key: Type[DataType], value: DataType) -> None:
        logger.debug("storing key:", key)
        if key in self._data:
            raise DuplicateStorageKeyError(key)

        self._data[key] = value

    def load(self, key: Type[DataType]) -> DataType:
        if key not in self._data:
            raise StorageKeyNotFoundError(key)

        return self._data[key]
