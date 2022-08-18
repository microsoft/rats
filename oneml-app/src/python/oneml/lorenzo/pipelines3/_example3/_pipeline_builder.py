# type: ignore
# flake8: noqa
from typing import Dict, Iterable, Set

from oneml.pipelines import PipelineNode, PipelineNodeClient, PipelineNodeDependenciesClient

from ._node_executable import PipelineNodeExecutable, PipelineNodeExecutablesClient
from ._pipeline_components import PipelineComponents
from ._pipeline_session_components import PipelineSessionComponentsFactory


class PipelineBuilder:

    _name: str
    _nodes: Set[PipelineNode]
    _dependencies: Dict[PipelineNode, Set[PipelineNode]]
    _executables: Dict[PipelineNode, PipelineNodeExecutable]

    def __init__(self, name: str):
        self._name = name
        self._nodes = set()
        self._dependencies = {}
        self._executables = {}

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

    def add_executable(self, node: PipelineNode, executable: PipelineNodeExecutable):
        if node in self._executables:
            raise RuntimeError(f"Duplicate node executable error: {node}")

        self._executables[node] = executable

    def build(self) -> PipelineComponents:
        node_client = PipelineNodeClient()
        dependencies_client = PipelineNodeDependenciesClient(node_client)
        executables_client = PipelineNodeExecutablesClient()

        for node in self._nodes:
            node_client.register_node(node)

            dependencies_client.register_node_dependencies(
                node, tuple(self._dependencies.get(node, []))
            )

            executables_client.register_node_executable(node, self._executables[node])

        return PipelineComponents(
            session_factory=PipelineSessionComponentsFactory(),
            node_client=node_client,
            dependencies_client=dependencies_client,
            executables_client=executables_client,
        )
