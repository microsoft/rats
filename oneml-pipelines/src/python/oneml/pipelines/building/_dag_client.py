from typing import Dict, Iterable, Set, Tuple

from oneml.pipelines.dag import (
    PipelineNode,
    IManagePipelineNodeDependencies,
    IManagePipelineNodes,
    PipelineNodeClient,
    PipelineNodeDependenciesClient, PipelineClient,
)


class PipelineDagClient:

    _nodes: Set[PipelineNode]
    _dependencies: Dict[PipelineNode, Set[PipelineNode]]

    def __init__(self) -> None:
        self._nodes = set()
        self._dependencies = {}

    def add_nodes(self, nodes: Iterable[PipelineNode]) -> None:
        for node in nodes:
            self.add_node(node)

    def add_node(self, node: PipelineNode) -> None:
        if node in self._nodes:
            raise RuntimeError(f"Duplicate node error: {node}")

        self._nodes.add(node)
        self._dependencies[node] = set()

    def add_dependencies(self, node: PipelineNode, dependencies: Iterable[PipelineNode]) -> None:
        for dependency in dependencies:
            self.add_dependency(node, dependency)

    def add_dependency(self, node: PipelineNode, dependency: PipelineNode) -> None:
        self._dependencies[node].add(dependency)

    def build(self) -> PipelineClient:
        node_client = PipelineNodeClient()
        dependencies_client = PipelineNodeDependenciesClient(node_client)

        for node in self._nodes:
            node_client.register_node(node)

            dependencies_client.register_node_dependencies(
                node, tuple(self._dependencies.get(node, [])))

        return PipelineClient(
            node_client=node_client,
            node_dependencies_client=dependencies_client,
        )
