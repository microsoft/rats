from __future__ import annotations

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
    """The combination of a [rats.apps.Container][] an [rats.apps.Executable][]."""

    def execute(self) -> None:
        """The main application entry point."""
        logger.warning(f"empty execute method in application: {self.__class__}")


class _AppPluginType(Protocol):
    @abstractmethod
    def __call__(self, app: Container) -> AppContainer:
        pass


class _ContainerPluginType(Protocol):
    @abstractmethod
    def __call__(self, app: Container) -> Container:
        pass


AppPlugin = _AppPluginType | Callable[[Container], AppContainer]
"""
Main interface for a function that returns an [rats.apps.AppContainer][] instance.

Functions that act as runners or application factories often take this as their input type in
order to manage the top most [rats.apps.Container][] instance, allowing most containers to use the
[rats.apps.PluginMixin][] mixin and rely on the top most container being managed automatically.
This is the companion type to [rats.apps.ContainerPlugin][].
"""

ContainerPlugin = _ContainerPluginType | Callable[[Container], Container]
"""
Factory function protocol that returns an [rats.apps.Container][] instance.
"""


class PluginMixin:
    """
    Mix into your [rats.apps.Container][] classes to add our default constructor.

    This mixin adds a common constructor to a `Container` in order to quickly create types that
    are compatible with functions asking for [rats.apps.AppPlugin][] and
    [rats.apps.ContainerPlugin][] arguments.

    !!! warning
        Avoid using mixins as an input type to your functions, because we don't want to restrict
        others to containers with a private `_app` property. Instead, use this as a shortcut to
        some commonly used implementation details.

    Example:
        ```python
         from rats import apps

         class ExampleApplication(apps.AppContainer, apps.PluginMixin):

            def execute() -> None:
                print("hello, world!")


        if __name__ == "__main__":
            apps.run_plugin(ExampleApplication)
        ```
    """

    _app: Container

    def __init__(self, app: Container) -> None:
        self._app = app


class CompositePlugin:
    """
    Similar to [rats.apps.CompositeContainer][] but takes a list of plugin container types.

    Example:
        ```python
        from rats import apps
        from rats_e2e.apps import inputs


        class ExamplePlugin1(apps.Container, apps.PluginMixin):
            pass


        class ExamplePlugin2(apps.Container, apps.PluginMixin):
            pass


        apps.run(
            apps.AppBundle(
                app_plugin=inputs.Application,
                container_plugin=apps.CompositePlugin(
                    ExamplePlugin1,
                    ExamplePlugin2,
                ),
            )
        )
        ```
    """

    _plugins: tuple[ContainerPlugin, ...]

    def __init__(self, *plugins: ContainerPlugin) -> None:
        self._plugins = plugins

    def __call__(self, app: Container) -> Container:
        return CompositeContainer(*[plugin(app) for plugin in self._plugins])


@final
class AppBundle(AppContainer):
    """
    Brings together different types of containers to construct an executable application.

    Use this class to defer the creation of an [rats.apps.AppContainer][] instance in order to
    combine services with additional [rats.apps.ContainerPlugin][] classes.
    """

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
        """
        Create an instance by providing the [rats.apps.AppPlugin][] type and any additional context.

        Example:
            ```python
            from rats import apps


            class ExamplePlugin(apps.Container, apps.PluginMixin):
                @apps.service(apps.ServiceId[str]("some-value"))
                def _some_value(self) -> str:
                    return "hello, world!"


            class ExampleApplication(apps.AppContainer, apps.PluginMixin):
                def execute(self) -> None:
                    print(self._app.get(apps.ServiceId[str]("some-value")))


            if __name__ == "__main__":
                apps.run(
                    apps.AppBundle(
                        app_plugin=ExampleApplication,
                        container_plugin=ExamplePlugin,
                    )
                )
            ```

        Args:
            app_plugin: the class reference to the application container.
            container_plugin: the class reference to an additional plugin container.
            context: an optional plugin container to make part of the container tree.
        """
        self._app_plugin = app_plugin
        self._container_plugin = container_plugin
        self._context = context

    def execute(self) -> None:
        """Initializes a new [rats.apps.AppContainer] with the provided nodes before executing it."""
        app, _ = self._get_or_create_containers()
        app.execute()

    @container()
    def _plugins(self) -> Container:
        return CompositeContainer(*self._get_or_create_containers(), self._context)

    @cache  # noqa: B019
    def _get_or_create_containers(self) -> tuple[AppContainer, Container]:
        return self._app_plugin(self), self._container_plugin(self)


class _EmptyAppContainer(AppContainer, PluginMixin):
    pass


EMPTY_APP_PLUGIN = _EmptyAppContainer


def bundle(
    *container_plugins: ContainerPlugin,
    context: Container = EMPTY_CONTEXT,
) -> Container:
    """
    Create an instance of a plugin container, without the need to create an application.

    Example:
        ```python
        from rats import apps, projects


        def main() -> None:
            apps.bundle(projects.PluginContainer)


        if __name__ == "__main__":
            main()
        ```

    Args:
        container_plugins: one or more plugins that will be initialized with an empty application.
        context: additional context made available to the container plugins.
    """
    return AppBundle(
        app_plugin=EMPTY_APP_PLUGIN,
        container_plugin=CompositePlugin(*container_plugins),
        context=context,
    )
