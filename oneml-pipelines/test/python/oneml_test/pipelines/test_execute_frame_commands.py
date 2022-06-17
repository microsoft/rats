from typing import List, Tuple

import pytest

from oneml.pipelines import (
    ExecutePipelineFrameCommand,
    IExecutePipelineNodes,
    PipelineNode,
    PipelineNodeState,
    PipelineNodeStateClient,
)


class FakeRunner(IExecutePipelineNodes):

    executed: List[PipelineNode]

    def __init__(self):
        self.executed = []

    def execute_node(self, node: PipelineNode) -> None:
        self.executed.append(node)


class TestExecutePipelineFrameCommand:

    _runner: FakeRunner
    _state_client: PipelineNodeStateClient
    _command: ExecutePipelineFrameCommand

    def setup(self) -> None:
        self._runner = FakeRunner()
        self._state_client = PipelineNodeStateClient()
        self._command = ExecutePipelineFrameCommand(
            runner=self._runner,
            state_client=self._state_client,
        )

    def test_basics(self) -> None:
        node1 = PipelineNode("fake-1")
        node2 = PipelineNode("fake-2")
        node3 = PipelineNode("fake-3")

        self._state_client.set_node_state(node1, PipelineNodeState.PENDING)
        self._state_client.set_node_state(node2, PipelineNodeState.QUEUED)
        self._state_client.set_node_state(node3, PipelineNodeState.PENDING)

        assert len(self._runner.executed) == 0
        self._command.execute()

    def test_no_runnable_nodes(self) -> None:
        node1 = PipelineNode("fake-1")
        node2 = PipelineNode("fake-2")
        node3 = PipelineNode("fake-3")

        self._state_client.set_node_state(node1, PipelineNodeState.QUEUED)
        self._state_client.set_node_state(node2, PipelineNodeState.QUEUED)
        self._state_client.set_node_state(node3, PipelineNodeState.QUEUED)

        with pytest.raises(RuntimeError):
            self._command.execute()
