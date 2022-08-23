import logging
from abc import abstractmethod
from typing import Dict, Protocol, Tuple

from ._structs import PipelineNode

logger = logging.getLogger(__name__)


class IRegisterPipelineNodes(Protocol):
    @abstractmethod
    def register_node(self, node: PipelineNode) -> None:
        """
        """


class ILocatePipelineNodes(Protocol):
    @abstractmethod
    def get_nodes(self) -> Tuple[PipelineNode, ...]:
        """
        """

    @abstractmethod
    def get_node_by_key(self, key: str) -> PipelineNode:
        """
        """


class IManagePipelineNodes(IRegisterPipelineNodes, ILocatePipelineNodes, Protocol):
    """
    """


class PipelineNodeClient(IManagePipelineNodes):

    _nodes: Dict[str, PipelineNode]

    def __init__(self) -> None:
        self._nodes = {}

    def register_node(self, node: PipelineNode) -> None:
        if node.key in self._nodes:
            raise DuplicatePipelineNodeError(node)

        self._nodes[node.key] = node

    def get_node_by_key(self, key: str) -> PipelineNode:
        if key not in self._nodes:
            raise NodeNotFoundError(key)

        return self._nodes[key]

    def get_nodes(self) -> Tuple[PipelineNode, ...]:
        return tuple(self._nodes.values())


class DuplicatePipelineNodeError(RuntimeError):

    node: PipelineNode

    def __init__(self, node: PipelineNode) -> None:
        super().__init__(f"Duplicate node registration: {node}")
        self.node = node


class NodeNotFoundError(RuntimeError):

    key: str

    def __init__(self, key: str) -> None:
        super().__init__(f"Node not found: {key}")
        self.key = key
