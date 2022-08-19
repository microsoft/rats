from functools import lru_cache
from typing import Iterable

from ._dag_client import PipelineDagClient, IPipelineDagClient
from ._executables_client import PipelineBuilderExecutablesClient, IManageBuilderExecutables, \
    IPipelineSessionExecutable
from ._node_multiplexing import PipelineNodeMultiplexerFactory, PipelineMultiplexValuesType, \
    PipelineNodeMultiplexer, IMultiplexPipelineNodes
from ._node_namespacing import PipelineNamespaceClient, INamespacePipelineNodes, \
    ICreatePipelineNamespaces
from oneml.pipelines.session import PipelineSessionClientFactory, PipelineSessionPluginClient
from oneml.pipelines.dag import PipelineNode, PipelineClient


class PipelineBuilderClient(
        IPipelineDagClient,
        IManageBuilderExecutables,
        ICreatePipelineNamespaces,
        INamespacePipelineNodes,
        IMultiplexPipelineNodes):

    def add_nodes(self, nodes: Iterable[PipelineNode]) -> None:
        self.get_dag_client().add_nodes(nodes)

    def add_node(self, node: PipelineNode) -> None:
        self.get_dag_client().add_node(node)

    def add_dependencies(self, node: PipelineNode, dependencies: Iterable[PipelineNode]) -> None:
        self.get_dag_client().add_dependencies(node, dependencies)

    def add_dependency(self, node: PipelineNode, dependency: PipelineNode) -> None:
        self.get_dag_client().add_dependency(node, dependency)

    def build(self) -> PipelineClient:
        return self.get_dag_client().build()

    def add_executable(
            self,
            node: PipelineNode,
            session_executable: IPipelineSessionExecutable) -> None:
        self.get_executables_client().add_executable(node, session_executable)

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

    def multiplex(self, values: PipelineMultiplexValuesType) -> PipelineNodeMultiplexer:
        return self.get_multiplex_client().get_instance(self.get_namespace_client(), values)

    @lru_cache()
    def get_namespace_client(self) -> PipelineNamespaceClient:
        return PipelineNamespaceClient("/")

    @lru_cache()
    def get_multiplex_client(self) -> PipelineNodeMultiplexerFactory:
        return PipelineNodeMultiplexerFactory(pipeline=self.get_dag_client())

    @lru_cache()
    def get_dag_client(self) -> PipelineDagClient:
        return PipelineDagClient()

    @lru_cache()
    def get_executables_client(self) -> PipelineBuilderExecutablesClient:
        return PipelineBuilderExecutablesClient(
            session_plugin_client=self.get_session_plugin_client(),
        )

    @lru_cache()
    def get_session_client_factory(self) -> PipelineSessionClientFactory:
        return PipelineSessionClientFactory(
            session_plugin_client=self.get_session_plugin_client())

    @lru_cache()
    def get_session_plugin_client(self) -> PipelineSessionPluginClient:
        return PipelineSessionPluginClient()


class PipelineBuilderFactory:

    def get_instance(self) -> PipelineBuilderClient:
        return PipelineBuilderClient()
