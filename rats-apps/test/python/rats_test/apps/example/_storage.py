"""
An example library that provides users with a storage client.

We pretend to require some storage settings, but the client stores data in memory so that we can write some simple tests.
"""
from typing_extensions import NamedTuple


class StorageSettings(NamedTuple):
    storage_account: str
    container: str


class StorageClient:

    # kept public to make testing easier
    settings: StorageSettings
    data: dict[str, str]

    def __init__(self, settings: StorageSettings) -> None:
        self.settings = settings
        self.data = {}

    def save(self, key: str, value: str) -> None:
        self.data[key] = value

    def load(self, key: str) -> str:
        return self.data[key]
