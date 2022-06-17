from oneml.pipelines import (
    ClosePipelineFrameCommand,
    IStopPipelines,
    PipelineNode,
    PipelineNodeState,
    PipelineNodeStateClient,
)


class FakeSession(IStopPipelines):

    calls: int

    def __init__(self):
        self.calls = 0

    def stop_pipeline(self) -> None:
        self.calls += 1


class TestClosePipelineFrameCommand:

    _session: FakeSession
    _state_client: PipelineNodeStateClient
    _command: ClosePipelineFrameCommand

    def setup(self) -> None:
        self._session = FakeSession()
        self._state_client = PipelineNodeStateClient()
        self._command = ClosePipelineFrameCommand(
            state_client=self._state_client,
            pipeline_session=self._session,
        )

    def test_complete_pipeline(self) -> None:
        node1 = PipelineNode("fake-1")
        node2 = PipelineNode("fake-2")
        node3 = PipelineNode("fake-3")

        self._state_client.set_node_state(node1, PipelineNodeState.COMPLETED)
        self._state_client.set_node_state(node2, PipelineNodeState.COMPLETED)
        self._state_client.set_node_state(node3, PipelineNodeState.COMPLETED)
        assert self._session.calls == 0
        self._command.execute()
        assert self._session.calls == 1

    def test_incomplete_pipeline(self) -> None:
        node1 = PipelineNode("fake-1")
        node2 = PipelineNode("fake-2")
        node3 = PipelineNode("fake-3")

        self._state_client.set_node_state(node1, PipelineNodeState.COMPLETED)
        self._state_client.set_node_state(node2, PipelineNodeState.PENDING)
        self._state_client.set_node_state(node3, PipelineNodeState.COMPLETED)
        assert self._session.calls == 0
        self._command.execute()
        assert self._session.calls == 0

