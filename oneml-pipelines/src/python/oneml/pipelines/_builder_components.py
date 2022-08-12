from functools import lru_cache

from ._builder import PipelineBuilder
from ._node_multiplexing import PipelineNodeMultiplexerFactory
from ._node_namespacing import PipelineNamespaceClient


class PipelineBuilderComponents:

    _pipeline_name: str

    def __init__(self, pipeline_name: str):
        self._pipeline_name = pipeline_name

    @lru_cache()
    def namespace_client(self) -> PipelineNamespaceClient:
        return PipelineNamespaceClient("/")

    @lru_cache()
    def multiplex_client(self) -> PipelineNodeMultiplexerFactory:
        return PipelineNodeMultiplexerFactory(pipeline=self.pipeline_builder())

    @lru_cache()
    def pipeline_builder(self) -> PipelineBuilder:
        return PipelineBuilder(name=self._pipeline_name)


class PipelineBuilderFactory:

    def get_instance(self, pipeline_name: str) -> PipelineBuilderComponents:
        return PipelineBuilderComponents(pipeline_name=pipeline_name)
