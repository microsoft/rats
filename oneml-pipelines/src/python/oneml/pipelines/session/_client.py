from functools import lru_cache

from oneml.pipelines.context._client import IProvideExecutionContexts
from oneml.pipelines.session import (
    IOManagerClient,
    IOManagerRegistry,
    PipelineSessionClient,
    PipelineSessionClientFactory,
    PipelineSessionPluginClient,
)
from oneml.pipelines.session._node_execution import PipelineNodeContext
from oneml.pipelines.session._services import ServicesRegistry
from oneml.pipelines.session._session_client import PipelineSessionContext


class PipelineSessionComponents:
    # TODO: maybe this should be our main session client class
    #       we need to make sure a factory actually creates proper independent sessions

    _services: ServicesRegistry
    _session_context: PipelineSessionContext
    _node_context: PipelineNodeContext
    # might want the data layer to be done with provider classes
    # so we can lazy load things a bit more
    _iomanager_client: IOManagerClient

    def __init__(
        self,
        services: ServicesRegistry,
        session_context: PipelineSessionContext,
        node_context: PipelineNodeContext,
        iomanager_client: IOManagerClient,
    ) -> None:
        self._services = services
        self._session_context = session_context
        self._node_context = node_context
        self._iomanager_client = iomanager_client

    def session_context(self) -> IProvideExecutionContexts[PipelineSessionClient]:
        return self._session_context

    @lru_cache()
    def session_client_factory(self) -> PipelineSessionClientFactory:
        return PipelineSessionClientFactory(
            session_context=self._session_context,
            node_context=self._node_context,
            services=self.services_registry(),
            iomanager_client=self._iomanager_client,
            session_plugin_client=self.session_plugin_client(),
        )

    @lru_cache()
    def session_plugin_client(self) -> PipelineSessionPluginClient:
        return PipelineSessionPluginClient()

    def services_registry(self) -> ServicesRegistry:
        return self._services

    def iomanager_registry(self) -> IOManagerRegistry:
        return self._iomanager_client.iomanager_registry()

    def iomanager_client(self) -> IOManagerClient:
        return self._iomanager_client
