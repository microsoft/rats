from rats.pipelines.dag import PipelineNode
from rats.pipelines.session import PipelineNodeState, PipelineNodeStateClient


class TestPipelineNodeStateClient:
    _client: PipelineNodeStateClient

    def setup_method(self) -> None:
        self._client = PipelineNodeStateClient(lambda: 1)

    def test_basics(self) -> None:
        node1 = PipelineNode("fake-1")
        node2 = PipelineNode("fake-2")
        node3 = PipelineNode("fake-3")
        node4 = PipelineNode("fake-4")

        self._client.set_node_state(node1, PipelineNodeState.QUEUED)
        self._client.set_node_state(node2, PipelineNodeState.QUEUED)
        self._client.set_node_state(node3, PipelineNodeState.RUNNING)
        self._client.set_node_state(node4, PipelineNodeState.COMPLETED)

        assert self._client.get_node_state(node1) == PipelineNodeState.QUEUED
        assert self._client.get_node_state(node3) == PipelineNodeState.RUNNING

        assert self._client.get_nodes_by_state(PipelineNodeState.QUEUED) == tuple([node1, node2])
        assert self._client.get_nodes_by_state(PipelineNodeState.RUNNING) == tuple([node3])
        assert self._client.get_nodes_by_state(PipelineNodeState.FAILED) == tuple()
