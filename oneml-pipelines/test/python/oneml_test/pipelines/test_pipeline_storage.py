import pytest

from oneml.pipelines import StorageClient, StorageItem, StorageItemKey


class FakeStorageItem:
    value: int

    def __init__(self, value: int):
        self.value = value


class TestStorageClient:

    _client: StorageClient

    def setup(self) -> None:
        self._client = StorageClient()

    def test_basics(self) -> None:
        item = FakeStorageItem(1)
        key = StorageItemKey("fake")

        self._client.publish_storage_item(StorageItem(key=key, value=item))

        assert self._client.get_storage_item(key) == item

    def test_missing_item(self) -> None:
        with pytest.raises(RuntimeError):
            self._client.get_storage_item(StorageItemKey("does-not-exist"))

    def test_duplicate_item(self) -> None:
        item = FakeStorageItem(1)
        key = StorageItemKey("fake")

        self._client.publish_storage_item(StorageItem(key=key, value=item))

        with pytest.raises(RuntimeError):
            self._client.publish_storage_item(StorageItem(key=key, value=item))
