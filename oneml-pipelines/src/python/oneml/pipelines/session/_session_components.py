from functools import lru_cache
from typing import Callable

from oneml.services import IProvideServices
from oneml.services._context import ContextClient

from ._running_session_registry import RunningSessionRegistry
from ._session_client_factory import PipelineSessionClientFactory
from ._session_data import SessionDataClient
from ._session_plugin_client import PipelineSessionPluginClient


class PipelineSessionComponents:
    # TODO: maybe this should be our main app client class
    #       we need to make sure a factory actually creates proper independent sessions

    _running_session_registry: RunningSessionRegistry
    _services: IProvideServices
    _context_client: ContextClient
    _session_data_client: SessionDataClient

    def __init__(
        self,
        running_session_registry: RunningSessionRegistry,
        services: IProvideServices,
        context_client: ContextClient,
        session_data_client: SessionDataClient,
    ) -> None:
        self._running_session_registry = running_session_registry
        self._services = services
        self._context_client = context_client
        self._session_data_client = session_data_client

    @lru_cache()
    def session_client_factory(self) -> PipelineSessionClientFactory:
        return PipelineSessionClientFactory(
            running_session_registry=self._running_session_registry,
            services=self.services_registry(),
            context_client=self._context_client,
            session_data_client=self.session_data_client(),
        )

    @lru_cache()
    def session_plugin_client_provider(self) -> Callable[[], PipelineSessionPluginClient]:
        return PipelineSessionPluginClient

    def services_registry(self) -> IProvideServices:
        return self._services

    def session_data_client(self) -> SessionDataClient:
        return self._session_data_client
