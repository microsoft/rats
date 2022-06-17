import logging

from ._executable import IExecutable
from ._node_dependencies import IManagePipelineNodeDependencies
from ._node_state import IManagePipelineNodeState, PipelineNodeState

logger = logging.getLogger(__name__)


class PromoteRegisteredNodesCommand(IExecutable):

    _state_client: IManagePipelineNodeState

    def __init__(self, state_client: IManagePipelineNodeState):
        self._state_client = state_client

    def execute(self) -> None:
        for node in self._state_client.get_nodes_by_state(PipelineNodeState.REGISTERED):
            self._state_client.set_node_state(node, PipelineNodeState.QUEUED)


class PromoteQueuedNodesCommand(IExecutable):

    _state_client: IManagePipelineNodeState
    _dependencies_client: IManagePipelineNodeDependencies

    def __init__(
            self,
            state_client: IManagePipelineNodeState,
            dependencies_client: IManagePipelineNodeDependencies):
        self._state_client = state_client
        self._dependencies_client = dependencies_client

    def execute(self) -> None:
        completed = self._state_client.get_nodes_by_state(PipelineNodeState.COMPLETED)
        queued = self._state_client.get_nodes_by_state(PipelineNodeState.QUEUED)
        # These nodes do not have any missing dependencies
        with_resolved_deps = self._dependencies_client.get_nodes_with_dependencies(completed)

        # All queued nodes without missing dependencies are runnable
        runnable = [x for x in queued if x in with_resolved_deps]
        for node in runnable:
            self._state_client.set_node_state(node, PipelineNodeState.PENDING)


class OpenPipelineFrameCommand(IExecutable):

    _promote_registered_command: IExecutable
    _promote_queued_command: IExecutable

    def __init__(
            self,
            promote_registered_command: IExecutable,
            promote_queued_command: IExecutable):
        self._promote_registered_command = promote_registered_command
        self._promote_queued_command = promote_queued_command

    def execute(self) -> None:
        self._promote_registered_command.execute()
        self._promote_queued_command.execute()
