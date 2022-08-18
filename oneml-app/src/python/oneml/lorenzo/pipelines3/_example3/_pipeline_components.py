# type: ignore
# flake8: noqa
from abc import abstractmethod
from functools import lru_cache
from typing import Protocol

from oneml.lorenzo.pipelines3._example3._node_executable import PipelineNodeExecutablesClient
from oneml.lorenzo.pipelines3._example3._pipeline_session import (
    DemoPipelineSessionFrame,
    PipelineSession,
)
from oneml.lorenzo.pipelines3._example3._pipeline_session_components import (
    PipelineSessionComponents,
    PipelineSessionComponentsFactory,
)
from oneml.pipelines import (
    ClosePipelineFrameCommand,
    ExecutePipelineFrameCommand,
    IManagePipelineNodeDependencies,
    IManagePipelineNodes,
    IManagePipelineNodeState,
    PipelineNodeClient,
    PipelineNodeDependenciesClient,
    PipelineNodeState,
    PipelineNodeStateClient,
    PipelineSessionStateClient,
    PromoteQueuedNodesCommand,
    PromoteRegisteredNodesCommand,
)


class IProvidePipelineComponents(Protocol):
    @abstractmethod
    def node_client(self) -> IManagePipelineNodes:
        pass

    @abstractmethod
    def dependencies_client(self) -> IManagePipelineNodeDependencies:
        pass

    @abstractmethod
    def executables_client(self) -> PipelineNodeExecutablesClient:
        pass


class PipelineComponents(IProvidePipelineComponents):
    _node_client: PipelineNodeClient
    _dependencies_client: PipelineNodeDependenciesClient
    _executables_client: PipelineNodeExecutablesClient
    _session_factory: PipelineSessionComponentsFactory

    def __init__(
        self,
        node_client: PipelineNodeClient,
        dependencies_client: PipelineNodeDependenciesClient,
        executables_client: PipelineNodeExecutablesClient,
        session_factory: PipelineSessionComponentsFactory,
    ):
        self._node_client = node_client
        self._dependencies_client = dependencies_client
        self._executables_client = executables_client
        self._session_factory = session_factory

    def node_client(self) -> IManagePipelineNodes:
        return self._node_client

    def dependencies_client(self) -> IManagePipelineNodeDependencies:
        return self._dependencies_client

    def executables_client(self) -> PipelineNodeExecutablesClient:
        return self._executables_client

    def session_components(self) -> PipelineSessionComponents:
        return self._session_factory.get_instance(
            nodes_client=self.node_client(),
            dependencies_client=self.dependencies_client(),
            executables_client=self.executables_client(),
        )
