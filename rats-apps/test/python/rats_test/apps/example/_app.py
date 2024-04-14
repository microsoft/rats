from collections.abc import Callable

from rats import apps
from rats.apps import Container
from rats.apps._composite_container import CompositeContainer
from rats.apps._plugin_container import PluginContainers


class ExampleApp(apps.AnnotatedContainer):
    _plugins: tuple[Callable[[Container], Container], ...]

    def __init__(self, *plugins: Callable[[Container], Container]):
        self._plugins = plugins

    @apps.container()
    def runtime_plugins(self) -> Container:
        return CompositeContainer(*[p(self) for p in self._plugins])

    @apps.container()
    def package_plugins(self) -> Container:
        return PluginContainers(self, "rats-apps.test-plugins")
