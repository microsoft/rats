import logging
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Generic, Protocol, TypeVar

logger = logging.getLogger(__name__)


OutputType = TypeVar("OutputType")


@dataclass(frozen=True)
class StorageItemKey(Generic[OutputType]):
    name: str


@dataclass(frozen=True)
class StorageItem(Generic[OutputType]):
    key: StorageItemKey[OutputType]
    value: OutputType


class ILocateStorageItems(Protocol):
    @abstractmethod
    def get_storage_item(self, key: StorageItemKey[OutputType]) -> OutputType:
        """ """


class IPublishStorageItems(Protocol):
    @abstractmethod
    def publish_storage_item(self, item: StorageItem[Any]) -> None:
        """ """


class IManageStorageItems(ILocateStorageItems, IPublishStorageItems, Protocol):
    """ """


class StorageClient(IManageStorageItems):

    _items: Dict[str, StorageItem[Any]]

    def __init__(self) -> None:
        self._items = {}

    def get_storage_item(self, key: StorageItemKey[OutputType]) -> OutputType:
        if key.name not in self._items:
            raise RuntimeError(f"Node output key not found: {key}")

        return self._items[key.name].value

    def publish_storage_item(self, item: StorageItem[Any]) -> None:
        if item.key.name in self._items:
            raise RuntimeError(f"Duplicate key found: {item.key}")

        self._items[item.key.name] = item
