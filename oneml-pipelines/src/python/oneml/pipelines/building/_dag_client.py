from abc import abstractmethod
from typing import Dict, Iterable, Protocol, Set

from oneml.pipelines.dag import (
    PipelineClient,
    PipelineNode,
    PipelineNodeClient,
    PipelineNodeDependenciesClient,
)
from oneml.pipelines.dag._data_dependencies_client import (
    PipelineDataDependenciesClient,
    PipelineDataDependency,
)


class IPipelineDagClient(Protocol):
    @abstractmethod
    def add_nodes(self, nodes: Iterable[PipelineNode]) -> None:
        pass

    @abstractmethod
    def add_node(self, node: PipelineNode) -> None:
        pass

    @abstractmethod
    def add_dependencies(self, node: PipelineNode, dependencies: Iterable[PipelineNode]) -> None:
        pass

    @abstractmethod
    def add_dependency(self, node: PipelineNode, dependency: PipelineNode) -> None:
        pass

    @abstractmethod
    def add_data_dependencies(
            self, node: PipelineNode, dependencies: Iterable[PipelineDataDependency]) -> None:
        pass

    @abstractmethod
    def add_data_dependency(self, node: PipelineNode, dependency: PipelineDataDependency) -> None:
        pass

    @abstractmethod
    def build(self) -> PipelineClient:
        pass


class PipelineDagClient(IPipelineDagClient):

    _nodes: Set[PipelineNode]
    _dependencies: Dict[PipelineNode, Set[PipelineNode]]
    _data_dependencies: Dict[PipelineNode, Set[PipelineDataDependency]]

    def __init__(self) -> None:
        self._nodes = set()
        self._dependencies = {}
        self._data_dependencies = {}

    def add_nodes(self, nodes: Iterable[PipelineNode]) -> None:
        for node in nodes:
            self.add_node(node)

    def add_node(self, node: PipelineNode) -> None:
        if node in self._nodes:
            raise RuntimeError(f"Duplicate node error: {node}")

        self._nodes.add(node)
        self._dependencies[node] = set()
        self._data_dependencies[node] = set()

    def add_dependencies(self, node: PipelineNode, dependencies: Iterable[PipelineNode]) -> None:
        for dependency in dependencies:
            self.add_dependency(node, dependency)

    def add_dependency(self, node: PipelineNode, dependency: PipelineNode) -> None:
        self._dependencies[node].add(dependency)

    def add_data_dependencies(
            self, node: PipelineNode, dependencies: Iterable[PipelineDataDependency]) -> None:
        for dependency in dependencies:
            self.add_data_dependency(node, dependency)

    def add_data_dependency(self, node: PipelineNode, dependency: PipelineDataDependency) -> None:
        self._data_dependencies[node].add(dependency)

    def build(self) -> PipelineClient:
        node_client = PipelineNodeClient()
        dependencies_client = PipelineNodeDependenciesClient(node_client)
        data_dependencies_client = PipelineDataDependenciesClient()

        for node in self._nodes:
            node_client.register_node(node)

            dependencies_client.register_node_dependencies(
                node, tuple(self._dependencies.get(node, [])))

            data_dependencies_client.register_data_dependencies(
                node, tuple(self._data_dependencies.get(node, [])))

        return PipelineClient(
            node_client=node_client,
            node_dependencies_client=dependencies_client,
            data_dependencies_client=data_dependencies_client,
        )
