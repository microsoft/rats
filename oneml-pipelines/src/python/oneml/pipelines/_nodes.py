from __future__ import annotations

import logging
from abc import abstractmethod
from dataclasses import dataclass
from typing import Dict, Protocol, Tuple

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PipelineNode:
    key: str


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


class IManagePipelineNodes(
        IRegisterPipelineNodes, ILocatePipelineNodes, Protocol):
    """
    """


class PipelineNodeClient(IManagePipelineNodes):

    _nodes: Dict[str, PipelineNode]

    def __init__(self) -> None:
        self._nodes = {}

    def register_node(self, node: PipelineNode) -> None:
        if node.key in self._nodes:
            raise RuntimeError(f"Node already registered: {node}")

        self._nodes[node.key] = node

    def get_node_by_key(self, key: str) -> PipelineNode:
        if key not in self._nodes:
            raise RuntimeError(f"Node not found: {key}")

        return self._nodes[key]

    def get_nodes(self) -> Tuple[PipelineNode, ...]:
        return tuple(self._nodes.values())
