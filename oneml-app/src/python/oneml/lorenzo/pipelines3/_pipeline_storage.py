import logging
from abc import abstractmethod
from dataclasses import dataclass
from typing import Dict, Generic, Protocol, TypeVar

logger = logging.getLogger(__name__)


OutputType = TypeVar("OutputType")


class IProvideStorageItemKeys(Protocol[OutputType]):
    @abstractmethod
    def get(self) -> str:
        pass


class StorageItemKey(IProvideStorageItemKeys, Generic[OutputType]):
    _name: str

    def __init__(self, name: str):
        self._name = name

    def get(self) -> str:
        return self._name


@dataclass(frozen=True)
class StorageItem(Generic[OutputType]):
    key: IProvideStorageItemKeys[OutputType]
    value: OutputType


class ILocateStorageItems(Protocol):
    @abstractmethod
    def get_storage_item(self, key: IProvideStorageItemKeys[OutputType]) -> OutputType:
        pass


class IPublishStorageItems(Protocol):
    @abstractmethod
    def publish_storage_item(self, item: StorageItem) -> None:
        pass


class IManageStorageItems(ILocateStorageItems, IPublishStorageItems, Protocol):
    pass


class StorageClient(IManageStorageItems):

    _items: Dict[str, StorageItem]

    def __init__(self):
        self._items = {}

    def get_storage_item(self, key: IProvideStorageItemKeys[OutputType]) -> OutputType:
        if key.get() not in self._items:
            raise RuntimeError(f"Node output key not found: {key}")

        return self._items[key.get()].value

    def publish_storage_item(self, item: StorageItem) -> None:
        if item.key in self._items:
            raise RuntimeError(f"Duplicate key found: {item.key}")

        self._items[item.key.get()] = item
