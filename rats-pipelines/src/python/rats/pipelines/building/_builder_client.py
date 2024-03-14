from collections.abc import Iterable
from functools import lru_cache
from typing import Any

from rats.pipelines.dag import (
    IAddPipelineDependencies,
    IAddPipelineNodes,
    IManagePipelineDags,
    PipelineDataDependency,
    PipelineNode,
)
from rats.pipelines.session import ISetPipelineNodeExecutables
from rats.services import IExecutable

from ._node_namespacing import (
    ICreatePipelineNamespaces,
    INamespacePipelineNodes,
    PipelineNamespaceClient,
)


# TODO: I don't know if we can maybe remove more code here
class PipelineBuilderClient(
    IAddPipelineNodes,
    IAddPipelineDependencies,
    ISetPipelineNodeExecutables,
    ICreatePipelineNamespaces,
    INamespacePipelineNodes,
):
    _dag_client: IManagePipelineDags
    _executables_client: ISetPipelineNodeExecutables

    def __init__(
        self,
        dag_client: IManagePipelineDags,
        executables_client: ISetPipelineNodeExecutables,
    ) -> None:
        self._dag_client = dag_client
        self._executables_client = executables_client

    def add_nodes(self, nodes: Iterable[PipelineNode]) -> None:
        self._dag_client.add_nodes(nodes)

    def add_node(self, node: PipelineNode) -> None:
        self._dag_client.add_node(node)

    def add_data_dependencies(
        self, node: PipelineNode, dependencies: Iterable[PipelineDataDependency[Any]]
    ) -> None:
        self._dag_client.add_data_dependencies(node, dependencies)

    def add_data_dependency(
        self, node: PipelineNode, dependency: PipelineDataDependency[Any]
    ) -> None:
        self._dag_client.add_data_dependency(node, dependency)

    def add_dependencies(self, node: PipelineNode, dependencies: Iterable[PipelineNode]) -> None:
        self._dag_client.add_dependencies(node, dependencies)

    def add_dependency(self, node: PipelineNode, dependency: PipelineNode) -> None:
        self._dag_client.add_dependency(node, dependency)

    def set_executable(self, node: PipelineNode, executable: IExecutable) -> None:
        self._executables_client.set_executable(node, executable)

    def namespace(self, name: str) -> PipelineNamespaceClient:
        return self.get_namespace_client().namespace(name)

    def nodes(self, names: Iterable[str]) -> Iterable[PipelineNode]:
        return self.get_namespace_client().nodes(names)

    def node(self, name: str) -> PipelineNode:
        return self.get_namespace_client().node(name)

    def head_node(self) -> PipelineNode:
        return self.get_namespace_client().head_node()

    def tail_node(self) -> PipelineNode:
        return self.get_namespace_client().tail_node()

    @lru_cache  # noqa: B019
    def get_namespace_client(self) -> PipelineNamespaceClient:
        # TODO: we can move this out to another service now!
        return PipelineNamespaceClient("/")
