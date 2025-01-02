from collections.abc import Iterator

from rats import apps

from ._ids import ExampleIds
from ._storage import StorageClient


class ExampleGroupsPlugin1(apps.Container, apps.PluginMixin):
    @apps.fallback_group(ExampleIds.GROUPS.STORAGE)
    def fallback_group_1(self) -> Iterator[StorageClient]:
        yield StorageClient(self._app.get(ExampleIds.CONFIGS.STORAGE))

    @apps.fallback_group(ExampleIds.GROUPS.STORAGE)
    def fallback_group_2(self) -> Iterator[StorageClient]:
        yield StorageClient(self._app.get(ExampleIds.CONFIGS.STORAGE))


class ExampleGroupsPlugin2(apps.Container, apps.PluginMixin):
    @apps.group(ExampleIds.GROUPS.STORAGE)
    def storage_group_1(self) -> Iterator[StorageClient]:
        yield StorageClient(self._app.get(ExampleIds.CONFIGS.STORAGE))
