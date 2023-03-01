from abc import abstractmethod
from functools import lru_cache
from typing import Protocol

from .building import PipelineBuilderClient
from .building._remote_execution import FakeRemoteExecutableFactory, IProvideRemoteExecutables
from .context._client import ContextClient, IManageExecutionContexts
from .dag import PipelineNode
from .data._memory_data_client import InMemoryDataClient
from .session import PipelineSessionClient
from .session._client import PipelineSessionComponents
from .session._node_execution import PipelineNodeContext
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


class PipelineFactory(Protocol):
    @abstractmethod
    def builder_client(self) -> PipelineBuilderClient:
        pass


class SimplePipelineFactory(PipelineFactory):

    def builder_client(self) -> PipelineBuilderClient:
        return PipelineBuilderClient(
            session_components=self._session_components(),
            pipeline_settings=self._pipeline_settings(),
            remote_executable_factory=self._remote_executable_factory(),
        )

    @lru_cache()
    def _remote_executable_factory(self) -> IProvideRemoteExecutables:
        return FakeRemoteExecutableFactory(session_context=self._pipeline_session_context())

    @lru_cache()
    def _session_components(self) -> PipelineSessionComponents:

        return PipelineSessionComponents(
            session_context=self._pipeline_session_context(),
            node_context=self._pipeline_node_context(),
            pipeline_data_client=self._pipeline_data_client(),
        )

    @lru_cache()
    def _pipeline_data_client(self) -> InMemoryDataClient:
        return InMemoryDataClient()

    @lru_cache()
    def _pipeline_settings(self) -> PipelineSettingsClient:
        return PipelineSettingsClient()

    @lru_cache()
    def _pipeline_session_context(self) -> PipelineSessionContext:
        return ContextClient[PipelineSessionClient]()

    @lru_cache()
    def _pipeline_node_context(self) -> PipelineNodeContext:
        return ContextClient[PipelineNode]()
