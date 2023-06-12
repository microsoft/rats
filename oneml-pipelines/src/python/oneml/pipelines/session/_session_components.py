from functools import lru_cache

from oneml.io._pipeline_data import IPipelineDataManager
from oneml.pipelines.session import PipelineSessionClientFactory, PipelineSessionPluginClient
from oneml.pipelines.session._services import ServicesRegistry


class PipelineSessionComponents:
    # TODO: maybe this should be our main app client class
    #       we need to make sure a factory actually creates proper independent sessions

    _services: ServicesRegistry
    _pipeline_data_client: IPipelineDataManager

    def __init__(
        self,
        services: ServicesRegistry,
        pipeline_data_client: IPipelineDataManager,
    ) -> None:
        self._services = services
        self._pipeline_data_client = pipeline_data_client

    @lru_cache()
    def session_client_factory(self) -> PipelineSessionClientFactory:
        return PipelineSessionClientFactory(
            services=self.services_registry(),
            pipeline_data_client=self._pipeline_data_client,
            session_plugin_client=self.session_plugin_client(),
        )

    @lru_cache()
    def session_plugin_client(self) -> PipelineSessionPluginClient:
        return PipelineSessionPluginClient()

    def services_registry(self) -> ServicesRegistry:
        return self._services

    def pipeline_data_client(self) -> IPipelineDataManager:
        return self._pipeline_data_client
