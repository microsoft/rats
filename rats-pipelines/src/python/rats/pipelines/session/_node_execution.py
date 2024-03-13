from abc import abstractmethod
from typing import Any, Protocol

from rats.pipelines.dag import PipelineNode
from rats.services import ContextProvider, IExecutable

from ._contexts import PipelineSession


class ILocatePipelineNodeExecutables(Protocol):
    @abstractmethod
    def get_executable(self, node: PipelineNode) -> IExecutable: ...


class ISetPipelineNodeExecutables(Protocol):
    @abstractmethod
    def set_executable(self, node: PipelineNode, executable: IExecutable) -> None: ...


class IExecutePipelineNodes(Protocol):
    @abstractmethod
    def execute_node(self, node: PipelineNode) -> None: ...


class IManagePipelineNodeExecutables(
    ILocatePipelineNodeExecutables,
    ISetPipelineNodeExecutables,
    IExecutePipelineNodes,
    Protocol,
):
    pass


class PipelineNodeExecutablesClient(IManagePipelineNodeExecutables):
    _executables: dict[Any, dict[PipelineNode, IExecutable]]
    _namespace: ContextProvider[PipelineSession]
    _node_ctx: ContextProvider[PipelineNode]

    def __init__(
        self,
        namespace: ContextProvider[PipelineSession],
        node_ctx: ContextProvider[PipelineNode],
    ) -> None:
        self._executables = {}
        self._namespace = namespace
        self._node_ctx = node_ctx

    def execute(self) -> None:
        self.execute_node(self._node_ctx())

    def execute_node(self, node: PipelineNode) -> None:
        self.get_executable(node).execute()

    def get_executable(self, node: PipelineNode) -> IExecutable:
        ctx = self._namespace()
        if node not in self._executables[ctx]:
            raise NodeExecutableNotFoundError(node)

        return self._executables[ctx][node]

    def set_executable(self, node: PipelineNode, executable: IExecutable) -> None:
        ctx = self._namespace()
        if ctx not in self._executables:
            self._executables[ctx] = {}

        if node in self._executables[ctx]:
            raise RuntimeError(f"Duplicate node executable: {node}")

        self._executables[ctx][node] = executable


class NodeExecutableNotFoundError(RuntimeError):
    node: PipelineNode

    def __init__(self, node: PipelineNode) -> None:
        self.node = node
        super().__init__(f"Executable not found for node: {node}")
