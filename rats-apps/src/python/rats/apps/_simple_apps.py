from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from typing import final

from ._annotations import fallback_service
from ._composite_container import CompositeContainer
from ._container import Container, container
from ._executables import App, Executable
from ._ids import ServiceId
from ._plugin_container import PluginContainers
from ._runtimes import Runtime, T_ExecutableType
from ._scoping import autoscope


class ExecutableCallableContext(Executable):
    """
    An executable that can be set dynamically with a callable.

    We use this class to support the use of `rats.apps` with a plain callable, like is expected of
    standard python scripts. We give this class a service id, and set the callable before using
    `apps.Runtime` to execute the chosen service id.
    """

    _exe_id: ServiceId[Executable]
    _callables: list[Callable[[], None]]

    def __init__(self, exe_id: ServiceId[Executable]) -> None:
        self._exe_id = exe_id
        self._callables = []

    def execute(self) -> None:
        if len(self._callables) == 0:
            raise RuntimeError("No active executable found.")

        self._callables[-1]()

    @contextmanager
    def open_callable(
        self,
        callable: Callable[[], None],
    ) -> Iterator[Executable]:
        self._callables.append(callable)
        try:
            yield App(callable)
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
    CALLABLE_EXE_CTX = ServiceId[ExecutableCallableContext]("callable-exe-ctx")
    CALLABLE_EXE = ServiceId[Executable]("callable-exe")


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

    def execute_callable(self, *callables: Callable[[], None]) -> None:
        ctx: ExecutableCallableContext = self._app.get(AppServices.CALLABLE_EXE_CTX)
        for cb in callables:
            with ctx.open_callable(cb) as exe:
                exe.execute()


@final
class SimpleApplication(Runtime, Container):
    """An application without anything fancy."""

    _plugin_groups: Iterable[str]

    def __init__(self, *plugin_groups: str) -> None:
        self._plugin_groups = plugin_groups

    def execute(self, *exe_ids: ServiceId[T_ExecutableType]) -> None:
        self._runtime().execute(*exe_ids)

    def execute_group(self, *exe_group_ids: ServiceId[T_ExecutableType]) -> None:
        self._runtime().execute_group(*exe_group_ids)

    def execute_callable(self, *callables: Callable[[], None]) -> None:
        for cb in callables:
            self._runtime().execute_callable(cb)

    @fallback_service(AppServices.RUNTIME)
    def _runtime(self) -> Runtime:
        """
        The default runtime is an instance of SimpleRuntime.

        Define a non-fallback service to override this default implementation.
        """
        return SimpleRuntime(self)

    @fallback_service(AppServices.CALLABLE_EXE)
    def _callable_exe(self) -> Executable:
        """We use the callable exe ctx here, so we can treat it like any other app downstream."""
        return self.get(AppServices.CALLABLE_EXE_CTX)

    @fallback_service(AppServices.CALLABLE_EXE_CTX)
    def _callable_exe_ctx(self) -> ExecutableCallableContext:
        """
        The default executable context client for executing raw callables.

        Define a non-fallback service to override this default implementation.
        """
        return ExecutableCallableContext(AppServices.CALLABLE_EXE)

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
