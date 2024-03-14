from abc import abstractmethod
from typing import Protocol

from ._executables import IExecutable, T_ExecutableType, after, before
from ._services import ServiceId
from ._typed_containers import TypedServiceContainer


class IExecuteServices(Protocol):
    @abstractmethod
    def execute_id(self, exe_id: ServiceId[T_ExecutableType]) -> None: ...

    @abstractmethod
    def execute(self, exe_id: ServiceId[T_ExecutableType], exe: IExecutable) -> None: ...

    @abstractmethod
    def execute_group(self, exe_id: ServiceId[T_ExecutableType]) -> None: ...


class ExecutablesClient(IExecuteServices):
    _container: TypedServiceContainer[IExecutable]

    def __init__(self, container: TypedServiceContainer[IExecutable]) -> None:
        self._container = container

    def execute_id(self, exe_id: ServiceId[T_ExecutableType]) -> None:
        self.execute(exe_id, self._container.get_service(exe_id.name))

    def execute(self, exe_id: ServiceId[T_ExecutableType], exe: IExecutable) -> None:
        self.execute_group(before(exe_id))
        exe.execute()
        self.execute_group(after(exe_id))

    def execute_group(self, exe_id: ServiceId[T_ExecutableType]) -> None:
        for exe in self._container.get_service_group(exe_id.name):
            exe.execute()
