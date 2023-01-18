from typing import Tuple

import pytest

from oneml.pipelines.dag import (
    ILocatePipelineNodes,
    NodeDependenciesRegisteredError,
    PipelineNode,
    PipelineNodeDependenciesClient,
)

node1 = PipelineNode("node-1")
node2 = PipelineNode("node-2")
node3 = PipelineNode("node-3")
node4 = PipelineNode("node-4")


class FakeNodeLocator(ILocatePipelineNodes):
    def get_nodes(self) -> Tuple[PipelineNode, ...]:
        return node1, node2, node3, node4

    def get_node_by_key(self, key: str) -> PipelineNode:
        # Just assume the node exists for the purpose of these tests
        return PipelineNode(key)


class TestPipelineNodeDependenciesClient:

    _client: PipelineNodeDependenciesClient

    def setup_method(self) -> None:
        self._client = PipelineNodeDependenciesClient(FakeNodeLocator())

    def test_dependency_registration(self) -> None:
        self._client.register_node_dependencies(node1, tuple([node2]))

        assert self._client.get_node_dependencies(node1) == tuple([node2])
        assert self._client.get_node_dependencies(node2) == tuple()

    def test_duplicate_dependency_errors(self) -> None:
        self._client.register_node_dependencies(node1, tuple([node2]))
        with pytest.raises(NodeDependenciesRegisteredError):
            self._client.register_node_dependencies(node1, tuple([node3]))

    def test_querying_dependencies(self) -> None:
        self._client.register_node_dependencies(node1, tuple([node2]))
        self._client.register_node_dependencies(node3, tuple([node1, node2]))
        self._client.register_node_dependencies(node4, tuple([node1]))

        result1 = self._client.get_nodes_with_dependencies(tuple([]))
        result2 = self._client.get_nodes_with_dependencies(tuple([node1]))
        result3 = self._client.get_nodes_with_dependencies(tuple([node2]))
        result4 = self._client.get_nodes_with_dependencies(tuple([node1, node2]))

        assert result1 == tuple(
            [node2]
        ), "Node 2 has no dependencies, so it basically always comes back"

        assert result2 == tuple(
            [node2, node4]
        ), "When Node 1 is complete, Nodes 2 and 4 are executable"

        assert result3 == tuple([node1]), "When Node 2 is complete, we can run Node 1"

        assert result4 == tuple(
            [node3, node4]
        ), "When Nodes 1 and 2 are complete, we can run Nodes 3 and 4"
