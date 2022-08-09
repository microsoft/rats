from functools import lru_cache

from ._nodes import PipelineNode
from ._pipeline_storage import IManageStorageItems, OutputType, StorageItem, StorageItemKey


class NodeStorageClient(IManageStorageItems):
    _parent_client: IManageStorageItems
    _node: PipelineNode

    def __init__(self, node: PipelineNode, parent_client: IManageStorageItems):
        self._node = node
        self._parent_client = parent_client

    def get_storage_item(self, key: StorageItemKey[OutputType]) -> OutputType:
        return self._parent_client.get_storage_item(self._namespaced_key(key))

    def publish_storage_item(self, item: StorageItem[OutputType]) -> None:
        self._parent_client.publish_storage_item(self._namespaced_item(item))

    @lru_cache()
    def _namespaced_item(self, output: StorageItem[OutputType]) -> StorageItem[OutputType]:
        return StorageItem(
            key=self._namespaced_key(output.key),
            value=output.value,
        )

    @lru_cache()
    def _namespaced_key(
            self, key: StorageItemKey[OutputType]) -> StorageItemKey[OutputType]:
        return StorageItemKey[OutputType](f"/{self._node.key}/{key.name}")


class NodeStorageClientFactory:
    _storage_client: IManageStorageItems

    def __init__(self, storage_client: IManageStorageItems):
        self._storage_client = storage_client

    @lru_cache()
    def get_instance(self, node: PipelineNode) -> NodeStorageClient:
        return NodeStorageClient(
            node=node,
            parent_client=self._storage_client
        )
