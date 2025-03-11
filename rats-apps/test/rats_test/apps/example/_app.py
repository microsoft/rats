from collections.abc import Callable

from rats import apps
from rats.apps import CompositeContainer, Container

from ._dummy_containers import DummyContainer
from ._storage_plugin import ExampleStoragePlugin


class ExampleApp(apps.Container):
    _plugins: tuple[Callable[[Container], Container], ...]

    def __init__(self, *plugins: Callable[[Container], Container]):
        self._plugins = plugins

    @apps.container()
    def dummy(self) -> Container:
        return DummyContainer(self)

    @apps.container()
    def runtime_plugins(self) -> Container:
        return CompositeContainer(*[p(self) for p in self._plugins])

    @apps.container()
    def package_plugins(self) -> Container:
        return ExampleStoragePlugin(self)
