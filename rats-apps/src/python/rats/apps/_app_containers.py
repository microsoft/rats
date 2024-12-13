import logging
from collections.abc import Callable
from functools import cache
from typing import Protocol, final

from rats import apps

logger = logging.getLogger(__name__)


class AppContainer(apps.Container, apps.Executable, Protocol):
    def execute(self) -> None:
        """The main application entry point."""
        logger.warning(f"empty execute method in application {self.__class__}")


AppPlugin = Callable[[apps.Container], AppContainer]


@final
class AppBundle(AppContainer):
    """Combine a context container and an application container to define the runtime environment."""

    _ctx: apps.Container
    _app_plugin: AppPlugin

    def __init__(
        self,
        ctx: apps.Container,
        app_plugin: AppPlugin,
    ):
        self._ctx = ctx
        self._app_plugin = app_plugin

    def execute(self) -> None:
        logger.debug(f"executing app bundle: {self._ctx} + {self._app_plugin}")
        self._get_or_create_app_container().execute()

    @apps.container()
    def _plugins(self) -> apps.Container:
        return apps.CompositeContainer(
            self._ctx,
            self._get_or_create_app_container(),
        )

    @cache  # noqa: B019
    def _get_or_create_app_container(self) -> AppContainer:
        return self._app_plugin(self)
