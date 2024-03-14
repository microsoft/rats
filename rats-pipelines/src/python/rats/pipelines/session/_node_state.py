from __future__ import annotations

import logging
from abc import abstractmethod
from enum import Enum, auto
from threading import RLock
from typing import Any, Protocol

from rats.pipelines.dag import PipelineNode
from rats.services import ContextProvider

logger = logging.getLogger(__name__)


class PipelineNodeState(Enum):
    NONE = auto()
    """
    Nodes that have just been inserted into the dag have no state.

    TODO: might be able to remove this soon since it's confusing.
    """

    REGISTERED = auto()
    """
    REGISTERED nodes have been registered on the current app's tick.

    A REGISTERED node can have other parts of the system adjust certain settings, like the node's
    dependencies, or runtime configuration.
    """

    QUEUED = auto()
    """
    QUEUED nodes have been validated and can no longer be configured.

    All nodes in the REGISTERED state will update to QUEUED on the next app's tick.
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
    def get_node_state(self, node: PipelineNode) -> PipelineNodeState: ...

    @abstractmethod
    def get_nodes_by_state(self, state: PipelineNodeState) -> tuple[PipelineNode, ...]: ...


class ISetPipelineNodeState(Protocol):
    @abstractmethod
    def set_node_state(self, node: PipelineNode, state: PipelineNodeState) -> None: ...


class IManagePipelineNodeState(ILocatePipelineNodeState, ISetPipelineNodeState, Protocol): ...


class PipelineNodeStateClient(IManagePipelineNodeState):
    _node_states: dict[Any, dict[PipelineNode, PipelineNodeState]]
    _context: ContextProvider[Any]

    def __init__(self, context: ContextProvider[Any]) -> None:
        self._node_states = {}
        self._lock = RLock()
        self._context = context

    def set_node_state(self, node: PipelineNode, state: PipelineNodeState) -> None:
        ctx = self._context()
        if ctx not in self._node_states:
            self._node_states[ctx] = {}

        with self._lock:
            self._node_states[ctx][node] = state

    def get_node_state(self, node: PipelineNode) -> PipelineNodeState:
        ctx = self._context()
        if ctx not in self._node_states:
            self._node_states[ctx] = {}

        with self._lock:
            # TODO: this hack needs to go and I think I can get rid of the NONE state
            return self._node_states[ctx].get(node, PipelineNodeState.NONE)

    def get_nodes_by_state(self, state: PipelineNodeState) -> tuple[PipelineNode, ...]:
        with self._lock:
            nodes = self._node_states.get(self._context(), {}).items()
            matches: list[PipelineNode] = []
            for node, node_state in nodes:
                if node_state == state:
                    matches.append(node)

        return tuple(matches)
