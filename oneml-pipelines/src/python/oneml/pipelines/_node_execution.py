from abc import abstractmethod
from typing import Dict, Protocol

from ._executable import IExecutable
from ._nodes import PipelineNode


class IExecutePipelineNodes(Protocol):
    @abstractmethod
    def execute_node(self, node: PipelineNode) -> None:
        """
        """


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
        IExecutePipelineNodes,
        Protocol):
    pass


# These classes below might be a good replacement for the executable concepts in oneml-pipelines
class PipelineNodeExecutablesClient(IManagePipelineNodeExecutables):

    _executables: Dict[PipelineNode, IExecutable]

    def __init__(self) -> None:
        self._executables = {}

    def execute_node(self, node: PipelineNode) -> None:
        self.get_node_executable(node).execute()

    def get_node_executable(self, node: PipelineNode) -> IExecutable:
        if node not in self._executables:
            raise RuntimeError(f"Node executable not found: {node}")

        return self._executables[node]

    def register_node_executable(
            self, node: PipelineNode, executable: IExecutable) -> None:
        if node in self._executables:
            raise RuntimeError(f"Duplicate node executable: {node}")

        self._executables[node] = executable
