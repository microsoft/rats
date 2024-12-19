import logging
from abc import abstractmethod
from collections.abc import Callable
from functools import cache
from typing import Protocol, final

from ._composite_container import CompositeContainer
from ._container import Container, container
from ._executables import Executable

logger = logging.getLogger(__name__)
EMPTY_CONTEXT = CompositeContainer()


def _empty_plugin(app: Container) -> Container:
    return CompositeContainer()


EMPTY_PLUGIN = _empty_plugin


class AppContainer(Container, Executable, Protocol):
    def execute(self) -> None:
        """The main application entry point."""
        logger.warning(f"empty execute method in application {self.__class__}")


class _AppPluginType(Protocol):
    @abstractmethod
    def __call__(self, app: Container) -> AppContainer:
        pass


class _ContainerPluginType(Protocol):
    @abstractmethod
    def __call__(self, app: Container) -> Container:
        pass


AppPlugin = _AppPluginType | Callable[[Container], AppContainer]
ContainerPlugin = _ContainerPluginType | Callable[[Container], Container]


class PluginMixin:
    """
    Mix into your `apps.Container` classes to add our default constructor.

    This mixin adds a common constructor to a `Container` in order to quickly create types that
    are compatible with functions asking for `AppPlugin` and `ContainerPlugin` arguments.

    !!! warning
        Avoid using mixins as an input type to your functions, because we don't want to restrict
        others to containers with a private `_app` property. Instead, use this as a shortcut to
        some commonly used implementation details.

    Examples:
         ```python
         from rats import apps

         class ExampleApplication(apps.AppContainer, apps.PluginMixin):

            def execute() -> None:
                print("hello, world!")


        if __name__ == "__main__":
            apps.run_main(ExampleApplication)
         ```
    """

    _app: Container

    def __init__(self, app: Container) -> None:
        self._app = app


class CompositePlugin:
    _plugins: tuple[ContainerPlugin, ...]

    def __init__(self, *plugins: ContainerPlugin) -> None:
        self._plugins = plugins

    def __call__(self, app: Container) -> Container:
        return CompositeContainer(*[plugin(app) for plugin in self._plugins])


@final
class AppBundle(AppContainer):
    """Brings together different types of containers to construct an executable application."""

    _app_plugin: AppPlugin
    _container_plugin: ContainerPlugin
    _context: Container

    def __init__(
        self,
        *,
        app_plugin: AppPlugin,
        container_plugin: ContainerPlugin = EMPTY_PLUGIN,
        context: Container = EMPTY_CONTEXT,
    ):
        self._app_plugin = app_plugin
        self._container_plugin = container_plugin
        self._context = context

    def execute(self) -> None:
        app, _ = self._get_or_create_containers()
        app.execute()

    @container()
    def _plugins(self) -> Container:
        return CompositeContainer(*self._get_or_create_containers(), self._context)

    @cache  # noqa: B019
    def _get_or_create_containers(self) -> tuple[AppContainer, Container]:
        return self._app_plugin(self), self._container_plugin(self)
