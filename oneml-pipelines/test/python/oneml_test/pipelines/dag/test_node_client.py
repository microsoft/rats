import pytest

from oneml.pipelines.dag import PipelineNode, PipelineNodeClient


class TestPipelineNodeClient:

    _client: PipelineNodeClient

    def setup_method(self) -> None:
        self._client = PipelineNodeClient()

    def test_basics(self) -> None:
        node1 = PipelineNode("fake-1")
        node2 = PipelineNode("fake-2")
        node3 = PipelineNode("fake-3")
        node4 = PipelineNode("fake-4")

        self._client.register_node(node1)
        self._client.register_node(node2)
        self._client.register_node(node3)
        self._client.register_node(node4)

        assert self._client.get_node_by_key("fake-1") == node1
        assert self._client.get_node_by_key("fake-2") == node2

    def test_get_nodes(self) -> None:
        node1 = PipelineNode("fake-1")
        node2 = PipelineNode("fake-2")
        node3 = PipelineNode("fake-3")
        node4 = PipelineNode("fake-4")

        self._client.register_node(node1)
        self._client.register_node(node2)
        self._client.register_node(node3)
        self._client.register_node(node4)

        assert self._client.get_nodes() == tuple(
            [
                node1,
                node2,
                node3,
                node4,
            ]
        )

    def test_validation(self) -> None:
        node1 = PipelineNode("fake-1")
        node2 = PipelineNode("fake-2")
        node3 = PipelineNode("fake-3")
        node4 = PipelineNode("fake-4")

        self._client.register_node(node1)
        self._client.register_node(node2)
        self._client.register_node(node3)
        self._client.register_node(node4)

        with pytest.raises(RuntimeError):
            self._client.register_node(node1)

        with pytest.raises(RuntimeError):
            self._client.get_node_by_key("fake-100")
