import logging

from ._executable import IExecutable
from ._node_state import IManagePipelineNodeState, PipelineNodeState
from ._pipelines import IStopPipelines

logger = logging.getLogger(__name__)


class ClosePipelineFrameCommand(IExecutable):

    _state_client: IManagePipelineNodeState
    _pipeline_session: IStopPipelines

    def __init__(self, state_client: IManagePipelineNodeState, pipeline_session: IStopPipelines):
        self._state_client = state_client
        self._pipeline_session = pipeline_session

    def execute(self) -> None:
        registered = self._state_client.get_nodes_by_state(PipelineNodeState.REGISTERED)
        queued = self._state_client.get_nodes_by_state(PipelineNodeState.QUEUED)
        pending = self._state_client.get_nodes_by_state(PipelineNodeState.PENDING)
        running = self._state_client.get_nodes_by_state(PipelineNodeState.RUNNING)

        for group in [registered, queued, pending, running]:
            if len(group) > 0:
                # Pipeline is not yet complete
                return

        logger.debug("No pending nodes remaining.")
        self._pipeline_session.stop_pipeline()
