import base64
import logging
import os
import pickle
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


class LocalDiskStorageClient(IManageStorageItems):
    def __init__(self, base_path: str) -> None:
        self._base_path = base_path

    def _key_to_path(self, key: StorageItemKey[OutputType]) -> str:
        filename = base64.urlsafe_b64encode(key.name.encode("UTF-8")).decode("UTF-8")
        path = os.path.join(self._base_path, filename)
        return path

    def get_storage_item(self, key: StorageItemKey[OutputType]) -> OutputType:
        path = self._key_to_path(key)
        with open(path, "rb") as fle:
            return pickle.load(fle)

    def publish_storage_item(self, item: StorageItem[Any]) -> None:
        path = self._key_to_path(item.key)
        with open(path, "wb") as fle:
            pickle.dump(item.value, fle)
