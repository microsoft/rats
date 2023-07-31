import logging
import uuid

from oneml.pipelines.dag import IManagePipelineDags
from oneml.services import IManageContexts

from ._contexts import OnemlSessionContexts, PipelineNodeContext
from ._node_execution import IExecutePipelineNodes
from ._node_state import IManagePipelineNodeState, PipelineNodeState
from ._session_state import IManagePipelineSessionState, PipelineSessionState

logger = logging.getLogger(__name__)


class PipelineSessionFrameClient:
    _context_client: IManageContexts
    _dag_client: IManagePipelineDags
    _session_state_client: IManagePipelineSessionState
    _node_state_client: IManagePipelineNodeState
    _node_executables_client: IExecutePipelineNodes

    def __init__(
        self,
        context_client: IManageContexts,
        dag_client: IManagePipelineDags,
        session_state_client: IManagePipelineSessionState,
        node_state_client: IManagePipelineNodeState,
        node_executables_client: IExecutePipelineNodes,
    ):
        self._context_client = context_client
        self._session_state_client = session_state_client
        self._node_state_client = node_state_client
        self._dag_client = dag_client
        self._node_executables_client = node_executables_client

    def tick(self) -> None:
        self._promote_new_nodes()
        self._promote_registered_nodes()
        self._promote_queued_nodes()
        self._execute_pending_nodes()
        self._check_pipeline_completion()

    def _promote_new_nodes(self) -> None:
        for node in self._dag_client.get_nodes():
            logger.debug(f"promoting new node {node}")
            if self._node_state_client.get_node_state(node) == PipelineNodeState.NONE:
                self._node_state_client.set_node_state(node, PipelineNodeState.REGISTERED)

    def _promote_registered_nodes(self) -> None:
        for node in self._node_state_client.get_nodes_by_state(PipelineNodeState.REGISTERED):
            logger.debug(f"promoting registered node {node}")
            self._node_state_client.set_node_state(node, PipelineNodeState.QUEUED)

    def _promote_queued_nodes(self) -> None:
        completed = self._node_state_client.get_nodes_by_state(PipelineNodeState.COMPLETED)
        queued = self._node_state_client.get_nodes_by_state(PipelineNodeState.QUEUED)
        # These nodes do not have any missing dependencies
        with_resolved_deps = self._dag_client.get_nodes_with_dependencies(completed)

        # All queued nodes without missing dependencies are runnable
        runnable = [x for x in queued if x in with_resolved_deps]
        logger.debug(f"promoting queued nodes {runnable}")
        for node in runnable:
            self._node_state_client.set_node_state(node, PipelineNodeState.PENDING)

    def _execute_pending_nodes(self) -> None:
        pending = self._node_state_client.get_nodes_by_state(PipelineNodeState.PENDING)
        if len(pending) == 0:
            # TODO: is having 0 pending nodes an exceptional case? I don't think so any more.
            return

        node = pending[0]

        with self._context_client.open_context(
            OnemlSessionContexts.PIPELINE_NODE,
            PipelineNodeContext(id=str(uuid.uuid4()), node=node),
        ):
            logger.debug(f"Executing node: {node}")
            self._node_state_client.set_node_state(node, PipelineNodeState.RUNNING)
            self._node_executables_client.execute_node(node)
            self._node_state_client.set_node_state(node, PipelineNodeState.COMPLETED)

        # TODO: put this threading logic somewhere
        # thread = Thread(target=self._execute_node, args=(node,))
        # thread.start()

    def _check_pipeline_completion(self) -> None:
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
