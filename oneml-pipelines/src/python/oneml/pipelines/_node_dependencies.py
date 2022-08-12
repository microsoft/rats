import logging
from abc import abstractmethod
from typing import Dict, Protocol, Tuple

from ._nodes import ILocatePipelineNodes, PipelineNode

logger = logging.getLogger(__name__)


class ILocatePipelineNodeDependencies(Protocol):
    @abstractmethod
    def get_node_dependencies(self, node: PipelineNode) -> Tuple[PipelineNode, ...]:
        """
        """

    @abstractmethod
    def get_nodes_with_dependencies(
            self,
            dependencies: Tuple[PipelineNode, ...]) -> Tuple[PipelineNode, ...]:
        """
        """


class IRegisterPipelineNodeDependencies(Protocol):
    @abstractmethod
    def register_node_dependencies(
            self, node: PipelineNode, dependencies: Tuple[PipelineNode, ...]) -> None:
        """
        """


class IManagePipelineNodeDependencies(
        ILocatePipelineNodeDependencies, IRegisterPipelineNodeDependencies, Protocol):
    """
    """


class PipelineNodeDependenciesClient(IManagePipelineNodeDependencies):

    _node_dependencies: Dict[PipelineNode, Tuple[PipelineNode, ...]]
    _node_client: ILocatePipelineNodes

    def __init__(self, node_client: ILocatePipelineNodes):
        self._node_dependencies = {}
        self._node_client = node_client

    def register_node_dependencies(
            self, node: PipelineNode, dependencies: Tuple[PipelineNode, ...]) -> None:
        if node in self._node_dependencies:
            raise NodeDependenciesRegisteredError(node)

        logger.debug(f"Setting node dependencies: {node} <- {dependencies}")
        self._node_dependencies[node] = dependencies

    def get_nodes_with_dependencies(
            self,
            dependencies: Tuple[PipelineNode, ...]) -> Tuple[PipelineNode, ...]:
        inbound_edges = set(dependencies)
        result = []

        for node in self._node_client.get_nodes():
            node_dependencies = self.get_node_dependencies(node)
            if node in dependencies:
                # Exclude the dependency nodes themselves
                continue

            node_edges = set(node_dependencies)
            if node_edges.issubset(inbound_edges):
                result.append(node)

        return tuple(result)

    def get_node_dependencies(self, node: PipelineNode) -> Tuple[PipelineNode, ...]:
        return self._node_dependencies.get(node, ())


class NodeDependenciesRegisteredError(RuntimeError):
    _node: PipelineNode

    def __init__(self, node: PipelineNode):
        super().__init__(f"Node dependencies already registered: {node}")
        self._node = node
