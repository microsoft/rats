from rats import apps

from ._ids import ExampleIds
from ._storage import StorageClient, StorageSettings


class ExampleGroupsPlugin1(apps.AnnotatedContainer):

    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.fallback_group(ExampleIds.GROUPS.STORAGE)
    def fallback_group_1(self) -> StorageClient:
        return StorageClient(self._app.get_config(ExampleIds.CONFIGS.STORAGE))

    @apps.fallback_group(ExampleIds.GROUPS.STORAGE)
    def fallback_group_2(self) -> StorageClient:
        return StorageClient(self._app.get_config(ExampleIds.CONFIGS.STORAGE))


class ExampleGroupsPlugin2(apps.AnnotatedContainer):

    _app: apps.Container

    def __init__(self, app: apps.Container) -> None:
        self._app = app

    @apps.group(ExampleIds.GROUPS.STORAGE)
    def storage_group_1(self) -> StorageClient:
        return StorageClient(self._app.get_config(ExampleIds.CONFIGS.STORAGE))
#
#
# class ExampleFallbackPlugin2(apps.AnnotatedContainer):
#
#     _app: apps.Container
#
#     def __init__(self, app: apps.Container) -> None:
#         self._app = app
#
#     @apps.service(ExampleIds.OTHER_STORAGE)
#     def other_storage(self) -> StorageClient:
#         return StorageClient(StorageSettings("other", "thing"))
#
#
# class ExampleFallbackPlugin3(apps.AnnotatedContainer):
#
#     _app: apps.Container
#
#     def __init__(self, app: apps.Container) -> None:
#         self._app = app
#
#     @apps.config(ExampleIds.CONFIGS.OTHER_STORAGE)
#     def other_storage_config(self) -> StorageSettings:
#         return StorageSettings("other", "thing")
