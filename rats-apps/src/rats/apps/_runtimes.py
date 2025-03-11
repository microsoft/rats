import logging
from abc import abstractmethod
from collections.abc import Callable
from typing import Protocol, final

from ._container import Container
from ._ids import ServiceId, T_ExecutableType

logger = logging.getLogger(__name__)


class Runtime(Protocol):
    """
    Classes that run services that implement the [rats.apps.Executable][] interface.

    Many of the lower level interfaces use [rats.apps.Executable][] to provide the user with a
    class that has an [rats.apps.Executable.execute][] method; most notably, [rats.apps.App][] and
    [rats.apps.AppContainer][]. These classes typically represent the main entry points to an
    application, and runtime implementations provide a way to execute these applications in
    threads, processes, and remote environments.
    """

    @abstractmethod
    def execute(self, *exe_ids: ServiceId[T_ExecutableType]) -> None:
        """Execute a list of executables sequentially."""

    @abstractmethod
    def execute_group(self, *exe_group_ids: ServiceId[T_ExecutableType]) -> None:
        """
        Execute one or more groups of executables sequentially.

        Although each group is expected to be executed sequentially, the groups themselves are not
        executed in a deterministic order. Runtime implementations are free to execute groups in
        parallel or in any order that is convenient.
        """


@final
class NullRuntime(Runtime):
    _msg: str

    def __init__(self, msg: str) -> None:
        self._msg = msg

    def execute(self, *exe_ids: ServiceId[T_ExecutableType]) -> None:
        logger.error(self._msg)
        raise NotImplementedError(f"NullRuntime cannot execute ids: {exe_ids}")

    def execute_group(self, *exe_group_ids: ServiceId[T_ExecutableType]) -> None:
        raise NotImplementedError(f"NullRuntime cannot execute groups: {exe_group_ids}")

    def execute_callable(self, *callables: Callable[[], None]) -> None:
        raise NotImplementedError(f"NullRuntime cannot execute callables: {callables}")


@final
class StandardRuntime(Runtime):
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
