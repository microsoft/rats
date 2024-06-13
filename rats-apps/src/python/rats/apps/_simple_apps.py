from collections.abc import Iterable
from typing import final

from ._annotations import fallback_service
from ._composite_container import CompositeContainer
from ._container import Container, container
from ._ids import ServiceId
from ._plugin_container import PluginContainers
from ._runtimes import Runtime, T_ExecutableType

DEFAULT_APP_CONTAINER = ServiceId[Container]("app-container")
DEFAULT_APP_RUNTIME = ServiceId[Runtime]("app-runtime")


@final
class SimpleRuntime(Runtime):
    """A simple runtime that executes sequentially and in a single thread."""

    _app: Container

    def __init__(self, app: Container) -> None:
        self._app = app

    def execute(self, *exe_ids: ServiceId[T_ExecutableType]) -> None:
        for exe_id in exe_ids:
            self._app.get(exe_id).execute()

    def execute_group(self, *exe_group_ids: ServiceId[T_ExecutableType]) -> None:
        for exe_group_id in exe_group_ids:
            for exe in self._app.get_group(exe_group_id):
                exe.execute()


@final
class SimpleApplication(Runtime, Container):
    """An application without anything fancy."""

    _plugin_groups: Iterable[str]

    def __init__(self, plugin_groups: Iterable[str]) -> None:
        self._plugin_groups = plugin_groups

    def execute(self, *exe_ids: ServiceId[T_ExecutableType]) -> None:
        self._runtime().execute(*exe_ids)

    def execute_group(self, *exe_group_ids: ServiceId[T_ExecutableType]) -> None:
        self._runtime().execute_group(*exe_group_ids)

    @fallback_service(DEFAULT_APP_RUNTIME)
    def _runtime(self) -> Runtime:
        """
        The default runtime is an instance of SimpleRuntime.

        Define a non-fallback service to override this default implementation.
        """
        return SimpleRuntime(self)

    @fallback_service(DEFAULT_APP_CONTAINER)
    def _container(self) -> Container:
        """
        The default container is the root application instance.

        Define a non-fallback service to override this default implementation.
        """
        return self

    @container()
    def _plugins(self) -> Container:
        return CompositeContainer(
            *[PluginContainers(self, group) for group in self._plugin_groups],
        )
