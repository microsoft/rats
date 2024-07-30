from rats import apps

from ._ids import ExampleIds
from ._storage import StorageClient, StorageSettings


class ExampleFallbackPlugin1(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.fallback_service(ExampleIds.OTHER_STORAGE)
    def fallback_other_storage(self) -> StorageClient:
        return StorageClient(self._app.get(ExampleIds.CONFIGS.OTHER_STORAGE))

    @apps.fallback_service(ExampleIds.CONFIGS.OTHER_STORAGE)
    def fallback_other_storage_config(self) -> StorageSettings:
        return StorageSettings("other[fallback]", "thing")


class ExampleFallbackPlugin2(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.service(ExampleIds.OTHER_STORAGE)
    def other_storage(self) -> StorageClient:
        return StorageClient(StorageSettings("other", "thing"))


class ExampleFallbackPlugin3(apps.Container):
    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.service(ExampleIds.CONFIGS.OTHER_STORAGE)
    def other_storage_config(self) -> StorageSettings:
        return StorageSettings("other", "thing")
