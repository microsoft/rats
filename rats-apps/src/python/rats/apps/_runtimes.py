from abc import abstractmethod
from collections.abc import Callable
from typing import Protocol, final

from ._ids import ServiceId, T_ExecutableType


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
        parallel or in any order that is convenient.
        """

    @abstractmethod
    def execute_callable(self, *callables: Callable[[], None]) -> None:
        """
        Execute provided callables by automatically turning them into apps.Executable objects.

        The used ServiceId is determined by the Runtime implementation.
        """


@final
class NullRuntime(Runtime):
    def execute(self, *exe_ids: ServiceId[T_ExecutableType]) -> None:
        raise NotImplementedError("NullRuntime does not support execution.")

    def execute_group(self, *exe_group_ids: ServiceId[T_ExecutableType]) -> None:
        raise NotImplementedError("NullRuntime does not support execution.")

    def execute_callable(self, *callables: Callable[[], None]) -> None:
        raise NotImplementedError("NullRuntime does not support execution.")
