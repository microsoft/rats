import logging

from rats.pipelines.dag import IManagePipelineDags
from rats.services import IExecutable, IManageContexts

from ._contexts import RatsSessionContexts
from ._node_state import IManagePipelineNodeState, PipelineNodeState
from ._session_state import IManagePipelineSessionState, PipelineSessionState

logger = logging.getLogger(__name__)


class PipelineSessionFrameClient(IExecutable):
    _context_client: IManageContexts
    _dag_client: IManagePipelineDags
    _session_state_client: IManagePipelineSessionState
    _node_state_client: IManagePipelineNodeState
    _execute_node: IExecutable

    def __init__(
        self,
        context_client: IManageContexts,
        dag_client: IManagePipelineDags,
        session_state_client: IManagePipelineSessionState,
        node_state_client: IManagePipelineNodeState,
        execute_node: IExecutable,
    ):
        self._context_client = context_client
        self._session_state_client = session_state_client
        self._node_state_client = node_state_client
        self._dag_client = dag_client
        self._execute_node = execute_node

    def execute(self) -> None:
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

        with self._context_client.open_context(RatsSessionContexts.NODE, node):
            logger.debug(f"Executing node: {node}")
            self._node_state_client.set_node_state(node, PipelineNodeState.RUNNING)
            self._execute_node.execute()
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
