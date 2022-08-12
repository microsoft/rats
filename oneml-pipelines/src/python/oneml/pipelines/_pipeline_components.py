from abc import abstractmethod
from typing import Protocol

from ._node_dependencies import IManagePipelineNodeDependencies, PipelineNodeDependenciesClient
from ._node_execution import PipelineNodeExecutablesClient
from ._nodes import IManagePipelineNodes, PipelineNodeClient
from ._session_components import PipelineSessionComponents, PipelineSessionComponentsFactory


class IProvidePipelineComponents(Protocol):

    @abstractmethod
    def node_client(self) -> IManagePipelineNodes:
        pass

    @abstractmethod
    def node_dependencies_client(self) -> IManagePipelineNodeDependencies:
        pass

    @abstractmethod
    def node_executables_client(self) -> PipelineNodeExecutablesClient:
        pass


class PipelineComponents(IProvidePipelineComponents):
    _node_client: PipelineNodeClient
    _node_dependencies_client: PipelineNodeDependenciesClient
    _node_executables_client: PipelineNodeExecutablesClient
    _session_factory: PipelineSessionComponentsFactory

    def __init__(
            self,
            node_client: PipelineNodeClient,
            node_dependencies_client: PipelineNodeDependenciesClient,
            node_executables_client: PipelineNodeExecutablesClient,
            session_factory: PipelineSessionComponentsFactory):
        self._node_client = node_client
        self._node_dependencies_client = node_dependencies_client
        self._node_executables_client = node_executables_client
        self._session_factory = session_factory

    def node_client(self) -> IManagePipelineNodes:
        return self._node_client

    def node_dependencies_client(self) -> IManagePipelineNodeDependencies:
        return self._node_dependencies_client

    def node_executables_client(self) -> PipelineNodeExecutablesClient:
        return self._node_executables_client

    def session_components(self) -> PipelineSessionComponents:
        return self._session_factory.get_instance(
            node_client=self.node_client(),
            node_dependencies_client=self.node_dependencies_client(),
            node_executables_client=self.node_executables_client(),
        )
