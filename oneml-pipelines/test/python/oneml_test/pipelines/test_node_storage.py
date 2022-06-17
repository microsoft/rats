from typing import Any, Dict

from oneml.pipelines import (
    IManageStorageItems,
    NodeStorageClient,
    NodeStorageClientFactory,
    OutputType,
    PipelineNode,
    StorageItem,
    StorageItemKey,
)


class FakeData:
    value: int

    def __init__(self, value: int):
        self.value = value


class FakeStorageClient(IManageStorageItems):

    items: Dict[Any, Any]

    def __init__(self):
        self.items = {}

    def get_storage_item(self, key: StorageItemKey[OutputType]) -> OutputType:
        return self.items[key].value

    def publish_storage_item(self, item: StorageItem) -> None:
        self.items[item.key] = item


class TestNodeStorageClient:

    _node1: PipelineNode
    _node2: PipelineNode

    _storage: FakeStorageClient

    _client1: NodeStorageClient
    _client2: NodeStorageClient

    def setup(self) -> None:
        self._node1 = PipelineNode("fake-node1")
        self._node2 = PipelineNode("fake-node2")

        self._storage = FakeStorageClient()
        self._client1 = NodeStorageClient(node=self._node1, parent_client=self._storage)
        self._client2 = NodeStorageClient(node=self._node2, parent_client=self._storage)

    def test_basics(self) -> None:
        key = StorageItemKey("fake-item")

        data1 = FakeData(1)
        data2 = FakeData(2)

        # We save different data using the same key
        item1 = StorageItem(key=key, value=data1)
        item2 = StorageItem(key=key, value=data2)

        # The data cannot go in the same storage client
        self._client1.publish_storage_item(item1)
        self._client2.publish_storage_item(item2)

        assert self._client1.get_storage_item(key) == data1
        assert self._client2.get_storage_item(key) == data2

        # Data ends up stored in the parent client without conflicts
        assert len(self._storage.items.keys()) == 2


class TestNodeStorageClientFactory:
    _factory: NodeStorageClientFactory

    def setup(self) -> None:
        self._factory = NodeStorageClientFactory(FakeStorageClient())

    def test_basics(self) -> None:
        self._factory.get_instance(PipelineNode("fake"))
