from functools import lru_cache

from oneml.pipelines.context._client import IManageExecutionContexts, IProvideExecutionContexts
from oneml.pipelines.session import (
    IManagePipelineData,
    PipelineSessionClient,
    PipelineSessionClientFactory,
    PipelineSessionPluginClient,
)
from oneml.pipelines.session._components import SessionComponents


class PipelineSessionComponents:
    # TODO: maybe this should be our main session client class
    #       we need to make sure a factory actually creates proper independent sessions

    _session_context: IManageExecutionContexts[PipelineSessionClient]
    # might want the data layer to be done with provider classes
    # so we can lazy load things a bit more
    _pipeline_data_client: IManagePipelineData

    def __init__(
        self,
        session_context: IManageExecutionContexts[PipelineSessionClient],
        pipeline_data_client: IManagePipelineData,
    ) -> None:
        self._session_context = session_context
        self._pipeline_data_client = pipeline_data_client

    def session_context(self) -> IProvideExecutionContexts[PipelineSessionClient]:
        return self._session_context

    @lru_cache()
    def session_client_factory(self) -> PipelineSessionClientFactory:
        return PipelineSessionClientFactory(
            session_context=self._session_context,
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
