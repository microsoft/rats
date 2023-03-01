from abc import abstractmethod
from typing import Dict, Protocol, TypeAlias

from oneml.pipelines.context._client import IManageExecutionContexts
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


PipelineNodeContext: TypeAlias = IManageExecutionContexts[PipelineNode]


class PipelineNodeExecutablesClient(IManagePipelineNodeExecutables, IExecutePipelineNodes):

    _executables: Dict[PipelineNode, IExecutable]
    _node_context: PipelineNodeContext

    def __init__(self, node_context: PipelineNodeContext) -> None:
        self._node_context = node_context
        self._executables = {}

    def get_active_node(self) -> PipelineNode:
        return self._node_context.get_context()

    def execute_node(self, node: PipelineNode) -> None:
        with self._node_context.execution_context(node):
            self.get_node_executable(node).execute()

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
