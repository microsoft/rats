from random import randint

from rats import apps

from ._ids import ExampleIds
from ._storage import StorageClient, StorageSettings


class ExampleStoragePlugin(apps.AnnotatedContainer):

    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.service(ExampleIds.STORAGE)
    def default_storage(self) -> StorageClient:
        return StorageClient(self._app.get(ExampleIds.CONFIGS.STORAGE))

    @apps.service(ExampleIds.DUPLICATE_SERVICE)
    def duplicate_1(self) -> StorageClient:
        return StorageClient(StorageSettings("fake", "fake"))

    @apps.service(ExampleIds.DUPLICATE_SERVICE)
    def duplicate_2(self) -> StorageClient:
        return StorageClient(StorageSettings("fake", "fake"))

    @apps.config(ExampleIds.CONFIGS.STORAGE)
    def default_storage_settings(self) -> StorageSettings:
        return StorageSettings("default", "default")

    @apps.config(ExampleIds.CONFIGS.RANDOM_STORAGE)
    def random_storage_settings(self) -> StorageSettings:
        return StorageSettings(f"random-{randint(1, 1000000)}", f"random-{randint(1, 1000000)}")

    @apps.config(ExampleIds.CONFIGS.DUPLICATE)
    def duplicate_config_1(self) -> StorageSettings:
        return StorageSettings("fake", "fake")

    @apps.config(ExampleIds.CONFIGS.DUPLICATE)
    def duplicate_config_2(self) -> StorageSettings:
        return StorageSettings("fake", "fake")
