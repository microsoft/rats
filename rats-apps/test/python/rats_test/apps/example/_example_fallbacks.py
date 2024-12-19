from rats import apps

from ._ids import ExampleIds
from ._storage import StorageClient, StorageSettings


class ExampleFallbackPlugin1(apps.Container, apps.PluginMixin):
    @apps.fallback_service(ExampleIds.OTHER_STORAGE)
    def fallback_other_storage(self) -> StorageClient:
        return StorageClient(self._app.get(ExampleIds.CONFIGS.OTHER_STORAGE))

    @apps.fallback_service(ExampleIds.CONFIGS.OTHER_STORAGE)
    def fallback_other_storage_config(self) -> StorageSettings:
        return StorageSettings("other[fallback]", "thing")


class ExampleFallbackPlugin2(apps.Container, apps.PluginMixin):
    @apps.service(ExampleIds.OTHER_STORAGE)
    def other_storage(self) -> StorageClient:
        return StorageClient(StorageSettings("other", "thing"))


class ExampleFallbackPlugin3(apps.Container, apps.PluginMixin):
    @apps.service(ExampleIds.CONFIGS.OTHER_STORAGE)
    def other_storage_config(self) -> StorageSettings:
        return StorageSettings("other", "thing")
