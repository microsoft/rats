from ._executables import IExecutable, T_ExecutableType, after, before
from ._services import ServiceGroupProvider, ServiceId
from ._typed_containers import TypedServiceContainer


class _ExecutableGroupExe(IExecutable):
    _group: ServiceGroupProvider[IExecutable]

    def __init__(self, group: ServiceGroupProvider[IExecutable]) -> None:
        self._group = group

    def execute(self) -> None:
        for exe in self._group():
            exe.execute()


class ExecutablesClient:
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
