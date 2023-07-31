from abc import abstractmethod
from typing import Any, Dict, Protocol

from oneml.pipelines.dag import PipelineNode
from oneml.services import ContextProvider, IExecutable


class ILocatePipelineNodeExecutables(Protocol):
    @abstractmethod
    def get_executable(self, node: PipelineNode) -> IExecutable:
        """ """


class ISetPipelineNodeExecutables(Protocol):
    @abstractmethod
    def set_executable(self, node: PipelineNode, executable: IExecutable) -> None:
        """ """


class IExecutePipelineNodes(Protocol):
    @abstractmethod
    def execute_node(self, node: PipelineNode) -> None:
        """ """


class IManagePipelineNodeExecutables(
    ILocatePipelineNodeExecutables,
    ISetPipelineNodeExecutables,
    IExecutePipelineNodes,
    Protocol,
):
    pass


class PipelineNodeExecutablesClient(IManagePipelineNodeExecutables):
    _executables: Dict[Any, Dict[PipelineNode, IExecutable]]
    _context: ContextProvider[Any]

    def __init__(self, context: ContextProvider[Any]) -> None:
        self._executables = {}
        self._context = context

    def execute_node(self, node: PipelineNode) -> None:
        self.get_executable(node).execute()

    def get_executable(self, node: PipelineNode) -> IExecutable:
        ctx = self._context()
        if node not in self._executables[ctx]:
            raise NodeExecutableNotFoundError(node)

        return self._executables[ctx][node]

    def set_executable(self, node: PipelineNode, executable: IExecutable) -> None:
        ctx = self._context()
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
