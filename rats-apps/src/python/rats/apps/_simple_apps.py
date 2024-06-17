from collections.abc import Generator, Iterable, Iterator
from contextlib import contextmanager
from typing import Callable, final

from ._annotations import fallback_service
from ._composite_container import CompositeContainer
from ._container import Container, container
from ._ids import ServiceId
from ._plugin_container import PluginContainers
from ._runtimes import Runtime, T_ExecutableType
from ._scoping import autoscope
from rats import apps


class ExecutableContextClient(apps.Executable):

    _exe_id: apps.ServiceId[apps.Executable]
    _callables = list[Callable[[], None]]

    def __init__(self, exe_id: apps.ServiceId[apps.Executable]) -> None:
        self._exe_id = exe_id
        self._callables = []

    def execute(self) -> None:
        if len(self._callables) == 0:
            raise RuntimeError("No active executable found.")

        self._callables[-1]()

    @contextmanager
    def open(self, callable: Callable[[], None]) -> Iterator[apps.Executable, None, None]:
        try:
            self._callables.append(callable)
            yield apps.App(callable)
        finally:
            self._callables.pop()


@autoscope
class AppServices:
    """
    Services used by simple apps that can generally be used anywhere.

    Owners of applications can decide not to use or not to make these services available to plugin
    authors.
    """

    RUNTIME = ServiceId[Runtime]("app-runtime")
    CONTAINER = ServiceId[Container]("app-container")
    RAW_EXE_CTX = ServiceId[ExecutableContextClient]("raw-exe-ctx")
    RAW_EXE = ServiceId[apps.Executable]("raw-exe")


@final
class SimpleRuntime(Runtime):
    """A simple runtime that executes sequentially and in a single thread."""

    _app: Container

    def __init__(self, app: Container) -> None:
        self._app = app

    def execute_callable(self, callable: Callable[[], None]) -> None:
        ctx = self._app.get(AppServices.RAW_EXE_CTX)
        with ctx.open(callable) as exe:
            exe.execute()

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

    def __init__(self, *plugin_groups: str) -> None:
        self._plugin_groups = plugin_groups

    def execute_callable(self, *callables: Callable[[], None]) -> None:
        for cb in callables:
            self._runtime().execute_callable(cb)

    def execute(self, *exe_ids: ServiceId[T_ExecutableType]) -> None:
        self._runtime().execute(*exe_ids)

    def execute_group(self, *exe_group_ids: ServiceId[T_ExecutableType]) -> None:
        self._runtime().execute_group(*exe_group_ids)

    @fallback_service(AppServices.RUNTIME)
    def _runtime(self) -> Runtime:
        """
        The default runtime is an instance of SimpleRuntime.

        Define a non-fallback service to override this default implementation.
        """
        return SimpleRuntime(self)

    @fallback_service(AppServices.RAW_EXE)
    def _raw_exe(self) -> apps.Executable:
        return self.get(AppServices.RAW_EXE_CTX)

    @fallback_service(AppServices.RAW_EXE_CTX)
    def _raw_exe_ctx(self) -> ExecutableContextClient:
        """
        The default executable context client for executing raw callables.

        Define a non-fallback service to override this default implementation.
        """
        return ExecutableContextClient(AppServices.RAW_EXE)

    @fallback_service(AppServices.CONTAINER)
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
