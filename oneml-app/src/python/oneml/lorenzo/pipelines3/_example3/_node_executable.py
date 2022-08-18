# type: ignore
# flake8: noqa
from abc import abstractmethod
from typing import Dict, Protocol

from oneml.pipelines import IExecutable, PipelineNode


class PipelineNodeExecutable(IExecutable, Protocol):
    pass


class IExecutePipelineNodes(Protocol):
    @abstractmethod
    def execute_node(self, node: PipelineNode) -> None:
        """ """


class ILocatePipelineNodeExecutables(Protocol):
    @abstractmethod
    def get_node_executable(self, node: PipelineNode) -> PipelineNodeExecutable:
        """ """


class IRegisterPipelineNodeExecutables(Protocol):
    @abstractmethod
    def register_node_executable(
        self, node: PipelineNode, executable: PipelineNodeExecutable
    ) -> None:
        """ """


class IManagePipelineNodeExecutables(
    ILocatePipelineNodeExecutables,
    IRegisterPipelineNodeExecutables,
    IExecutePipelineNodes,
    Protocol,
):
    pass


# These classes below might be a good replacement for the executable concepts in oneml-pipelines
class PipelineNodeExecutablesClient(IManagePipelineNodeExecutables):

    _executables: Dict[PipelineNode, PipelineNodeExecutable]

    def __init__(self):
        self._executables = {}

    def execute_node(self, node: PipelineNode) -> None:
        self.get_node_executable(node).execute()

    def get_node_executable(self, node: PipelineNode) -> PipelineNodeExecutable:
        return self._executables[node]

    def register_node_executable(
        self, node: PipelineNode, executable: PipelineNodeExecutable
    ) -> None:
        if node in self._executables:
            raise RuntimeError(f"Diplicate node executable: {node}")

        self._executables[node] = executable
