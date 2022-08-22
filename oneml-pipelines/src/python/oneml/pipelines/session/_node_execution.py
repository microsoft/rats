from abc import abstractmethod
from typing import Dict, Protocol

from oneml.pipelines.dag import PipelineNode

from ._executable import IExecutable


class ILocatePipelineNodeExecutables(Protocol):
    @abstractmethod
    def get_node_executable(self, node: PipelineNode) -> IExecutable:
        """
        """


class IRegisterPipelineNodeExecutables(Protocol):
    @abstractmethod
    def register_node_executable(
            self, node: PipelineNode, executable: IExecutable) -> None:
        """
        """


class IManagePipelineNodeExecutables(
        ILocatePipelineNodeExecutables,
        IRegisterPipelineNodeExecutables,
        Protocol):
    pass


class IExecutePipelineNodes(Protocol):
    @abstractmethod
    def execute_node(self, node: PipelineNode) -> None:
        """
        """


class PipelineNodeExecutablesClient(IManagePipelineNodeExecutables, IExecutePipelineNodes):

    _executables: Dict[PipelineNode, IExecutable]

    def __init__(self) -> None:
        self._executables = {}

    def execute_node(self, node: PipelineNode) -> None:
        self.get_node_executable(node).execute()

    def get_node_executable(self, node: PipelineNode) -> IExecutable:
        if node not in self._executables:
            raise NodeExecutableNotFoundError(node)

        return self._executables[node]

    def register_node_executable(
            self, node: PipelineNode, executable: IExecutable) -> None:
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
