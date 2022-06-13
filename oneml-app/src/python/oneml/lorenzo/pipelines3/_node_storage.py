from functools import lru_cache

from ._nodes import PipelineNode
from ._pipeline_storage import (
    IManageStorageItems,
    IProvideStorageItemKeys,
    OutputType,
    StorageItem,
    StorageItemKey,
)


class NodeStorageClient(IManageStorageItems):
    _parent_client: IManageStorageItems
    _node: PipelineNode

    def __init__(self, node: PipelineNode, parent_client: IManageStorageItems):
        self._node = node
        self._parent_client = parent_client

    def get_storage_item(self, key: IProvideStorageItemKeys[OutputType]) -> OutputType:
        return self._parent_client.get_storage_item(self._namespaced_key(key))

    def publish_storage_item(self, item: StorageItem) -> None:
        self._parent_client.publish_storage_item(self._namespaced_item(item))

    @lru_cache()
    def _namespaced_item(self, output: StorageItem) -> StorageItem:
        return StorageItem(
            key=self._namespaced_key(output.key),
            value=output.value,
        )

    @lru_cache()
    def _namespaced_key(
            self, key: IProvideStorageItemKeys[OutputType]) -> IProvideStorageItemKeys[OutputType]:
        return StorageItemKey[OutputType](f"/{self._node.key}/{key.get()}")


class NodeStorageClientFactory:
    _storage_client: IManageStorageItems

    @lru_cache()
    def get_instance(self, node: PipelineNode) -> NodeStorageClient:
        return NodeStorageClient(
            node=node,
            parent_client=self._storage_client
        )
