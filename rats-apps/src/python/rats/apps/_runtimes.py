from abc import abstractmethod
from typing import Protocol, TypeVar

from ._container import Container
from ._executables import Executable
from ._ids import ServiceId

T_ExecutableType = TypeVar("T_ExecutableType", bound=Executable)


class Runtime(Protocol):
    @abstractmethod
    def execute(self, *exe_ids: ServiceId[T_ExecutableType]) -> None:
        """Execute a list of executables sequentially."""

    @abstractmethod
    def execute_group(self, *exe_group_ids: ServiceId[T_ExecutableType]) -> None:
        """
        Execute one or more groups of executables sequentially.

        Although each group is expected to be executed sequentially, the groups themselves are not
        executed in a deterministic order. Runtime implementations are free to execute groups in
        parallel or in any other order that is convenient.
        """


class SimpleRuntime(Runtime):
    """A simple runtime that executes sequentially and in a single thread."""

    _app: Container

    def execute(self, *exe_ids: ServiceId[Executable]) -> None:
        for exe_id in exe_ids:
            self._app.get(exe_id).execute()

    def execute_group(self, *exe_group_ids: ServiceId[Executable]) -> None:
        for exe_group_id in exe_group_ids:
            for exe in self._app.get_group(exe_group_id):
                exe.execute()
