import logging
from threading import Thread

from ._executable import IExecutable
from ._node_execution import IExecutePipelineNodes
from ._node_state import IManagePipelineNodeState, PipelineNodeState
from ._nodes import PipelineNode

logger = logging.getLogger(__name__)


class ExecutePipelineFrameCommand(IExecutable):

    _state_client: IManagePipelineNodeState
    _runner: IExecutePipelineNodes

    def __init__(self, state_client: IManagePipelineNodeState, runner: IExecutePipelineNodes):
        self._state_client = state_client
        self._runner = runner

    def _execute_node(self, node: PipelineNode) -> None:
        self._runner.execute_node(node)
        self._state_client.set_node_state(node, PipelineNodeState.COMPLETED)

    def execute(self) -> None:
        pending = self._state_client.get_nodes_by_state(PipelineNodeState.PENDING)
        if len(pending) == 0:
            return

        node = pending[0]
        self._state_client.set_node_state(node, PipelineNodeState.RUNNING)
        thread = Thread(target=self._execute_node, args=(node,))
        thread.start()
