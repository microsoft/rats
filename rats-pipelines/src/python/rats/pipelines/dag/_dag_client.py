from abc import abstractmethod
from collections.abc import Iterable
from typing import Any, Protocol

from rats.services import ContextProvider

from ._structs import PipelineDataDependency, PipelineNode


class IAddPipelineNodes(Protocol):
    def add_nodes(self, nodes: Iterable[PipelineNode]) -> None:
        for node in nodes:
            self.add_node(node)

    @abstractmethod
    def add_node(self, node: PipelineNode) -> None:
        pass


class IGetPipelineNodes(Protocol):
    @abstractmethod
    def get_nodes(self) -> frozenset[PipelineNode]: ...


class IManagePipelineNodes(IAddPipelineNodes, IGetPipelineNodes, Protocol): ...


class IAddPipelineDependencies(Protocol):
    def add_data_dependencies(
        self, node: PipelineNode, dependencies: Iterable[PipelineDataDependency[Any]]
    ) -> None:
        for dependency in dependencies:
            self.add_data_dependency(node, dependency)

    @abstractmethod
    def add_data_dependency(
        self, node: PipelineNode, dependency: PipelineDataDependency[Any]
    ) -> None:
        pass

    def add_dependencies(self, node: PipelineNode, dependencies: Iterable[PipelineNode]) -> None:
        for dependency in dependencies:
            self.add_dependency(node, dependency)

    @abstractmethod
    def add_dependency(self, node: PipelineNode, dependency: PipelineNode) -> None:
        pass


class IGetPipelineDependencies(Protocol):
    @abstractmethod
    def get_nodes_with_dependencies(
        self, dependencies: tuple[PipelineNode, ...]
    ) -> frozenset[PipelineNode]:
        pass

    @abstractmethod
    def get_node_dependencies(self, node: PipelineNode) -> frozenset[PipelineNode]:
        pass

    @abstractmethod
    def get_data_dependencies(self, node: PipelineNode) -> frozenset[PipelineDataDependency[Any]]:
        pass


class IManagePipelineDependencies(IAddPipelineDependencies, IGetPipelineDependencies, Protocol):
    pass


class IManagePipelineDags(IManagePipelineNodes, IManagePipelineDependencies, Protocol):
    pass


class PipelineDagClient(IManagePipelineDags):
    _nodes: dict[Any, set[PipelineNode]]
    _dependencies: dict[Any, dict[PipelineNode, set[PipelineNode]]]
    _data_dependencies: dict[Any, dict[PipelineNode, set[PipelineDataDependency[Any]]]]

    _context: ContextProvider[Any]

    def __init__(self, context: ContextProvider[Any]) -> None:
        self._nodes = {}
        self._dependencies = {}
        self._data_dependencies = {}

        self._context = context

    def add_node(self, node: PipelineNode) -> None:
        ctx = self._context()
        if ctx not in self._nodes:
            self._nodes[ctx] = set()
            self._dependencies[ctx] = {}
            self._data_dependencies[ctx] = {}

        if node in self._nodes[ctx]:
            raise RuntimeError(f"Duplicate node error: {node}")

        self._nodes[ctx].add(node)
        self._dependencies[ctx][node] = set()
        self._data_dependencies[ctx][node] = set()

    def add_data_dependency(
        self, node: PipelineNode, dependency: PipelineDataDependency[Any]
    ) -> None:
        ctx = self._context()
        self._data_dependencies[ctx][node].add(dependency)
        self.add_dependency(node, dependency.node)

    def add_dependency(self, node: PipelineNode, dependency: PipelineNode) -> None:
        ctx = self._context()
        self._dependencies[ctx][node].add(dependency)

    def get_nodes_with_dependencies(
        self, dependencies: tuple[PipelineNode, ...]
    ) -> frozenset[PipelineNode]:
        inbound_edges = set(dependencies)
        result: list[PipelineNode] = []

        for node in self.get_nodes():
            node_dependencies = self.get_node_dependencies(node)
            if node in dependencies:
                # Exclude the dependency nodes themselves
                continue

            node_edges = set(node_dependencies)
            if node_edges.issubset(inbound_edges):
                result.append(node)

        return frozenset(result)

    def get_node_dependencies(self, node: PipelineNode) -> frozenset[PipelineNode]:
        ctx = self._context()
        return frozenset(self._dependencies[ctx].get(node, ()))

    def get_data_dependencies(self, node: PipelineNode) -> frozenset[PipelineDataDependency[Any]]:
        ctx = self._context()
        return frozenset(self._data_dependencies[ctx].get(node, ()))

    def get_nodes(self) -> frozenset[PipelineNode]:
        return frozenset(self._nodes.get(self._context(), set()))


class NodeDependenciesRegisteredError(RuntimeError):
    _node: PipelineNode

    def __init__(self, node: PipelineNode):
        super().__init__(f"Node dependencies already registered: {node}")
        self._node = node
