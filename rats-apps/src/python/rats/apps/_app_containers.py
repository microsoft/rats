import logging
from abc import abstractmethod
from functools import cache
from typing import Protocol, final

from ._composite_container import CompositeContainer
from ._executables import Executable
from ._container import Container, container

logger = logging.getLogger(__name__)
EMPTY_CONTEXT = CompositeContainer()


def _empty_plugin(app: Container) -> Container:
    return CompositeContainer()


EMPTY_PLUGIN = _empty_plugin


class AppContainer(Container, Executable, Protocol):
    def execute(self) -> None:
        """The main application entry point."""
        logger.warning(f"empty execute method in application {self.__class__}")


class AppPlugin(Protocol):
    """Protocol representing Callable[[Container], AppContainer]."""

    __name__: str

    @abstractmethod
    def __call__(self, app: Container) -> AppContainer:
        pass


class ContainerPlugin(Protocol):
    """Protocol representing Callable[[Container], Container]."""

    @abstractmethod
    def __call__(self, app: Container) -> Container:
        pass


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
