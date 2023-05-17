from functools import lru_cache
from typing import Protocol

from .building import DefaultDataTypeMapper, IPipelineBuilderFactory, PipelineBuilderClient
from .building._remote_execution import FakeRemoteExecutableFactory, IProvideRemoteExecutables
from .context._client import ContextClient, IManageExecutionContexts
from .dag import PipelineNode
from .data._memory_data_client import InMemoryDataClient
from .session import IOManagerClient, IOManagerRegistry, PipelineSessionClient
from .session._client import PipelineSessionComponents
from .session._node_execution import PipelineNodeContext
from .session._services import ServicesRegistry
from .session._session_client import PipelineSessionContext
from .settings import PipelineSettingsClient


class IProvidePipelineComponents(Protocol):
    @lru_cache()
    def builder_client(self) -> PipelineBuilderClient:
        pass

    @lru_cache()
    def remote_executable_factory(self) -> IProvideRemoteExecutables:
        pass

    @lru_cache()
    def session_components(self) -> PipelineSessionComponents:
        pass

    @lru_cache()
    def pipeline_data_client(self) -> InMemoryDataClient:
        pass

    @lru_cache()
    def pipeline_settings(self) -> PipelineSettingsClient:
        pass

    @lru_cache()
    def pipeline_session_context(self) -> IManageExecutionContexts[PipelineSessionClient]:
        pass


class SimplePipelineFactory(IPipelineBuilderFactory):
    _services: ServicesRegistry
    _iomanagers: IOManagerRegistry
    _default_datatype_mapper: DefaultDataTypeMapper
    _session_context: PipelineSessionContext

    def __init__(
        self,
        services: ServicesRegistry,
        iomanagers: IOManagerRegistry,
        default_datatype_mapper: DefaultDataTypeMapper,
        session_context: PipelineSessionContext,
    ):
        self._services = services
        self._iomanagers = iomanagers
        self._default_datatype_mapper = default_datatype_mapper
        self._session_context = session_context

    def get_instance(self) -> PipelineBuilderClient:
        return PipelineBuilderClient(
            session_components=self._create_session_components(),
            pipeline_settings=self._create_pipeline_settings(),
            remote_executable_factory=self._create_remote_executable_factory(),
        )

    def get_default_datatype_mapper(self) -> DefaultDataTypeMapper:
        return self._default_datatype_mapper

    def _create_remote_executable_factory(self) -> IProvideRemoteExecutables:
        return FakeRemoteExecutableFactory(session_context=self._session_context)

    def _create_session_components(self) -> PipelineSessionComponents:
        return PipelineSessionComponents(
            services=self._services,
            session_context=self._session_context,
            node_context=self._create_pipeline_node_context(),
            iomanager_client=self._create_iomanager_client(),
        )

    def _create_inmemory_pipeline_data_client(self) -> InMemoryDataClient:
        return InMemoryDataClient()

    def _create_iomanager_client(self) -> IOManagerClient:
        return IOManagerClient(
            iomanager_registry=self._iomanagers,
            default=self._create_inmemory_pipeline_data_client(),
        )

    def _create_pipeline_settings(self) -> PipelineSettingsClient:
        return PipelineSettingsClient()

    def _create_pipeline_node_context(self) -> PipelineNodeContext:
        return ContextClient[PipelineNode]()
