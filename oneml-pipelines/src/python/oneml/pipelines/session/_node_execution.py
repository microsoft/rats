from abc import abstractmethod
from contextlib import contextmanager
from typing import Dict, Generator, Optional, Protocol

from oneml.pipelines.dag import PipelineNode

from ._executable import IExecutable


class ILocateActiveNodes(Protocol):
    @abstractmethod
    def get_active_node(self) -> PipelineNode:
        """ """


class ILocatePipelineNodeExecutables(Protocol):
    @abstractmethod
    def get_node_executable(self, node: PipelineNode) -> IExecutable:
        """ """


class IRegisterPipelineNodeExecutables(Protocol):
    @abstractmethod
    def register_node_executable(self, node: PipelineNode, executable: IExecutable) -> None:
        """ """


class IExecutePipelineNodes(Protocol):
    @abstractmethod
    def execute_node(self, node: PipelineNode) -> None:
        """ """


class IManagePipelineNodeExecutables(
    ILocatePipelineNodeExecutables,
    ILocateActiveNodes,
    IRegisterPipelineNodeExecutables,
    IExecutePipelineNodes,
    Protocol,
):
    pass


class PipelineNodeExecutablesClient(IManagePipelineNodeExecutables, IExecutePipelineNodes):

    _executables: Dict[PipelineNode, IExecutable]
    _active_node: Optional[PipelineNode]

    def __init__(self) -> None:
        self._executables = {}
        self._active_node = None

    def get_active_node(self) -> PipelineNode:
        if not self._active_node:
            raise RuntimeError("No active node")
        return self._active_node

    def execute_node(self, node: PipelineNode) -> None:
        with self.execution_context(node):
            self.get_node_executable(node).execute()

    @contextmanager
    def execution_context(self, node: PipelineNode) -> Generator[None, None, None]:
        current = self._active_node
        self._active_node = node
        try:
            yield
        finally:
            self._active_node = current

    def get_node_executable(self, node: PipelineNode) -> IExecutable:
        if node not in self._executables:
            raise NodeExecutableNotFoundError(node)

        return self._executables[node]

    def register_node_executable(self, node: PipelineNode, executable: IExecutable) -> None:
        if node in self._executables:
            raise RuntimeError(f"Duplicate node executable: {node}")

        self._executables[node] = executable


#
# class CompositePipelineNodeExecutablesClient(ILocatePipelineNodeExecutables):
#
#     _clients: Tuple[ILocatePipelineNodeExecutables, ...]
#
#     def __init__(self, clients: Tuple[ILocatePipelineNodeExecutables, ...]) -> None:
#         self._clients = clients
#
#     def get_node_executable(self, node: PipelineNode) -> IExecutable:
#         for client in self._clients:
#             try:
#                 return client.get_node_executable(node)
#             except NodeExecutableNotFoundError:
#                 pass
#
#         raise NodeExecutableNotFoundError(node)


class NodeExecutableNotFoundError(RuntimeError):

    node: PipelineNode

    def __init__(self, node: PipelineNode) -> None:
        self.node = node
        super().__init__(f"Executable not found for node: {node}")
