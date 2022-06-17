from __future__ import annotations

import logging
from abc import abstractmethod
from enum import Enum, auto
from typing import Dict, Protocol, Tuple

from ._nodes import PipelineNode

logger = logging.getLogger(__name__)


class PipelineNodeState(Enum):
    # TODO: Use binary values so we can query by combinations of states.

    REGISTERED = auto()
    """
    REGISTERED nodes have been registered on the current session's tick.
    
    A REGISTERED node can have other parts of the sistem adjust certain settings, like the node's
    dependencies, or runtime configuration.
    """

    QUEUED = auto()
    """
    QUEUED nodes have been validated and can no longer be configured.

    All nodes in the REGISTERED state will update to QUEUED on the next session's tick.
    """

    PENDING = auto()
    """
    PENDING nodes have met all required criteria for being submitted to a runtime environment.

    The criteria for promoting a node from QUEUED to PENDING is pipeline specific. For example, we
    can require a node's dependencies to be in a COMPLETED state.
    """

    RUNNING = auto()
    """
    RUNNING nodes have been submitted to the runtime environment.
    """

    COMPLETED = auto()
    FAILED = auto()


class ILocatePipelineNodeState(Protocol):
    @abstractmethod
    def get_node_state(self, node: PipelineNode) -> PipelineNodeState:
        """
        """

    @abstractmethod
    def get_nodes_by_state(self, state: PipelineNodeState) -> Tuple[PipelineNode, ...]:
        """
        """


class ISetPipelineNodeState(Protocol):
    @abstractmethod
    def set_node_state(self, node: PipelineNode, state: PipelineNodeState) -> None:
        """
        """


class IManagePipelineNodeState(ILocatePipelineNodeState, ISetPipelineNodeState, Protocol):
    """
    """


class PipelineNodeStateClient(IManagePipelineNodeState):

    _node_states: Dict[PipelineNode, PipelineNodeState]

    def __init__(self):
        self._node_states = {}

    def set_node_state(self, node: PipelineNode, state: PipelineNodeState) -> None:
        self._node_states[node] = state

    def get_node_state(self, node: PipelineNode) -> PipelineNodeState:
        return self._node_states[node]

    def get_nodes_by_state(self, state: PipelineNodeState) -> Tuple[PipelineNode, ...]:
        matches = []
        for node, node_state in self._node_states.items():
            if node_state == state:
                matches.append(node)

        return tuple(matches)
