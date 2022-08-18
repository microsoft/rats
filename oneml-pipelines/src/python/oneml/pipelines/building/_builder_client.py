from functools import lru_cache

from ._dag_client import PipelineDagClient
from ._executables_client import PipelineBuilderExecutablesClient
from ._node_multiplexing import PipelineNodeMultiplexerFactory
from ._node_namespacing import PipelineNamespaceClient
from oneml.pipelines.session import PipelineSessionClientFactory, PipelineSessionPluginClient


class PipelineBuilderClient:

    @lru_cache()
    def namespace_client(self) -> PipelineNamespaceClient:
        return PipelineNamespaceClient("/")

    @lru_cache()
    def multiplex_client(self) -> PipelineNodeMultiplexerFactory:
        return PipelineNodeMultiplexerFactory(pipeline=self.dag())

    @lru_cache()
    def dag(self) -> PipelineDagClient:
        return PipelineDagClient()

    @lru_cache()
    def executables(self) -> PipelineBuilderExecutablesClient:
        return PipelineBuilderExecutablesClient(
            session_plugin_client=self.session_plugin_client(),
        )

    @lru_cache()
    def session_factory(self) -> PipelineSessionClientFactory:
        return PipelineSessionClientFactory(
            session_plugin_client=self.session_plugin_client())

    @lru_cache()
    def session_plugin_client(self) -> PipelineSessionPluginClient:
        return PipelineSessionPluginClient()


class PipelineBuilderFactory:

    def get_instance(self) -> PipelineBuilderClient:
        return PipelineBuilderClient()
