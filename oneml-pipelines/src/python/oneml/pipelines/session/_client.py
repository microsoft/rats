from functools import lru_cache

from oneml.pipelines.context._client import IProvideExecutionContexts
from oneml.pipelines.session import (
    IManagePipelineData,
    PipelineSessionClient,
    PipelineSessionClientFactory,
    PipelineSessionPluginClient,
)
from oneml.pipelines.session._components import SessionComponents
from oneml.pipelines.session._node_execution import PipelineNodeContext
from oneml.pipelines.session._session_client import PipelineSessionContext


class PipelineSessionComponents:
    # TODO: maybe this should be our main session client class
    #       we need to make sure a factory actually creates proper independent sessions

    _session_context: PipelineSessionContext
    _node_context: PipelineNodeContext
    # might want the data layer to be done with provider classes
    # so we can lazy load things a bit more
    _pipeline_data_client: IManagePipelineData

    def __init__(
        self,
        session_context: PipelineSessionContext,
        node_context: PipelineNodeContext,
        pipeline_data_client: IManagePipelineData,
    ) -> None:
        self._session_context = session_context
        self._node_context = node_context
        self._pipeline_data_client = pipeline_data_client

    def session_context(self) -> IProvideExecutionContexts[PipelineSessionClient]:
        return self._session_context

    @lru_cache()
    def session_client_factory(self) -> PipelineSessionClientFactory:
        return PipelineSessionClientFactory(
            session_context=self._session_context,
            node_context=self._node_context,
            components=self.session_components(),
            pipeline_data_client=self._pipeline_data_client,
            session_plugin_client=self.session_plugin_client(),
        )

    @lru_cache()
    def session_plugin_client(self) -> PipelineSessionPluginClient:
        return PipelineSessionPluginClient()

    @lru_cache()
    def session_components(self) -> SessionComponents:
        return SessionComponents()

    def pipeline_data_client(self) -> IManagePipelineData:
        return self._pipeline_data_client
