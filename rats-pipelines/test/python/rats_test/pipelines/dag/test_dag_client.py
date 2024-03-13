from rats.pipelines.dag import PipelineDagClient, PipelineNode


class TestPipelineDagClient:
    _client: PipelineDagClient

    def setup_method(self) -> None:
        self._client = PipelineDagClient(lambda: 1)

    def test_basics(self) -> None:
        node1 = PipelineNode("fake-1")
        node2 = PipelineNode("fake-2")
        node3 = PipelineNode("fake-3")
        node4 = PipelineNode("fake-4")

        self._client.add_node(node1)
        self._client.add_node(node2)
        self._client.add_node(node3)
        self._client.add_node(node4)

        assert self._client.get_nodes() == {node1, node2, node3, node4}
