import logging
from abc import abstractmethod
from typing import Protocol, Tuple

from oneml.pipelines.dag import IManagePipelineNodeDependencies
from oneml.pipelines.session._executable import IExecutable
from oneml.pipelines.session._node_execution import IExecutePipelineNodes
from oneml.pipelines.session._node_state import IManagePipelineNodeState, PipelineNodeState
from oneml.pipelines.session._session_state import IManagePipelineSessionState, \
    PipelineSessionState

logger = logging.getLogger(__name__)


class IPipelineSessionFrame(Protocol):
    @abstractmethod
    def tick(self) -> None:
        """"""


class BasicPipelineSessionFrameCommands:

    _session_state_client: IManagePipelineSessionState
    _node_state_client: IManagePipelineNodeState
    _node_dependencies_client: IManagePipelineNodeDependencies
    _node_executables_client: IExecutePipelineNodes

    def __init__(
            self,
            session_state_client: IManagePipelineSessionState,
            node_state_client: IManagePipelineNodeState,
            node_dependencies_client: IManagePipelineNodeDependencies,
            node_executables_client: IExecutePipelineNodes):
        self._session_state_client = session_state_client
        self._node_state_client = node_state_client
        self._node_dependencies_client = node_dependencies_client
        self._node_executables_client = node_executables_client

    def promote_registered_nodes(self) -> None:
        for node in self._node_state_client.get_nodes_by_state(PipelineNodeState.REGISTERED):
            self._node_state_client.set_node_state(node, PipelineNodeState.QUEUED)

    def promote_queued_nodes(self) -> None:
        completed = self._node_state_client.get_nodes_by_state(PipelineNodeState.COMPLETED)
        queued = self._node_state_client.get_nodes_by_state(PipelineNodeState.QUEUED)
        # These nodes do not have any missing dependencies
        with_resolved_deps = self._node_dependencies_client.get_nodes_with_dependencies(completed)

        # All queued nodes without missing dependencies are runnable
        runnable = [x for x in queued if x in with_resolved_deps]
        for node in runnable:
            self._node_state_client.set_node_state(node, PipelineNodeState.PENDING)

    def execute_pending_nodes(self) -> None:
        pending = self._node_state_client.get_nodes_by_state(PipelineNodeState.PENDING)
        logger.debug(f"Pending nodes: {pending}")
        if len(pending) == 0:
            # TODO: is having 0 pending nodes an exceptional case?
            return

        node = pending[0]

        logger.debug(f"Executing node: {node}")
        self._node_state_client.set_node_state(node, PipelineNodeState.RUNNING)
        self._node_executables_client.execute_node(node)
        self._node_state_client.set_node_state(node, PipelineNodeState.COMPLETED)

        # TODO: put this threading logic somewhere
        # thread = Thread(target=self._execute_node, args=(node,))
        # thread.start()

    def check_pipeline_completion(self) -> None:
        registered = self._node_state_client.get_nodes_by_state(PipelineNodeState.REGISTERED)
        queued = self._node_state_client.get_nodes_by_state(PipelineNodeState.QUEUED)
        pending = self._node_state_client.get_nodes_by_state(PipelineNodeState.PENDING)
        running = self._node_state_client.get_nodes_by_state(PipelineNodeState.RUNNING)

        for group in [registered, queued, pending, running]:
            if len(group) > 0:
                # Pipeline is not yet complete
                return

        logger.debug("No pending nodes remaining.")
        self._session_state_client.set_state(PipelineSessionState.STOPPED)


class PipelineSessionFrame(IPipelineSessionFrame):
    # TODO: turn these ideas into lifecycle events and tools to group events (pre/post)
    _frame_commands: Tuple[IExecutable, ...]

    def __init__(self, frame_commands: Tuple[IExecutable, ...]) -> None:
        self._frame_commands = frame_commands

    def tick(self) -> None:
        logger.debug("running pipeline frame tick()")
        for command in self._frame_commands:
            command.execute()
