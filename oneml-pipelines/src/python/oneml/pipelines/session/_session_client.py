from abc import abstractmethod
from typing import Any, Iterable, Protocol

from oneml.services._context import ContextClient

from ...io import IGetLoaders, IGetPublishers
from ...services import IProvideServices, ServiceId, ServiceProvider, ServiceType
from ..dag import PipelineNode, PipelineSessionId
from ._context import OnemlSessionContextIds
from ._node_execution import IManagePipelineNodeExecutables
from ._node_state import IManagePipelineNodeState
from ._running_session_registry import RunningSessionRegistry
from ._session_frame import IPipelineSessionFrame
from ._session_state import IManagePipelineSessionState, PipelineSessionState


class IRunnablePipelineSession(Protocol):
    @abstractmethod
    def run(self) -> None:
        pass


class IStoppablePipelineSession(Protocol):
    @abstractmethod
    def stop(self) -> None:
        pass


class IPipelineSession(IRunnablePipelineSession, IStoppablePipelineSession, Protocol):
    pass


class PipelineSessionClient(IPipelineSession, IProvideServices):
    _running_session_registry: RunningSessionRegistry
    _session_id: PipelineSessionId
    _services: IProvideServices
    _context_client: ContextClient
    _session_frame: IPipelineSessionFrame
    _session_executables_client: IManagePipelineNodeExecutables
    _session_state_client: IManagePipelineSessionState
    _node_state_client: IManagePipelineNodeState
    _node_executables_client: IManagePipelineNodeExecutables
    _pipeline_loader_getter: IGetLoaders[Any]
    _pipeline_publisher_getter: IGetPublishers[Any]

    def __init__(
        self,
        running_session_registry: RunningSessionRegistry,
        session_id: PipelineSessionId,
        services: IProvideServices,
        context_client: ContextClient,
        session_frame: IPipelineSessionFrame,
        session_state_client: IManagePipelineSessionState,
        session_executables_client: IManagePipelineNodeExecutables,
        node_state_client: IManagePipelineNodeState,
        node_executables_client: IManagePipelineNodeExecutables,
        pipeline_loader_getter: IGetLoaders[Any],
        pipeline_publisher_getter: IGetPublishers[Any],
    ):
        self._running_session_registry = running_session_registry
        self._session_id = session_id
        self._services = services
        self._context_client = context_client
        self._session_frame = session_frame
        self._session_state_client = session_state_client
        self._session_executables_client = session_executables_client
        self._node_state_client = node_state_client
        self._node_executables_client = node_executables_client
        self._pipeline_loader_getter = pipeline_loader_getter
        self._pipeline_publisher_getter = pipeline_publisher_getter

    def get_service(self, component_id: ServiceId[ServiceType]) -> ServiceType:
        return self._services.get_service(component_id)

    def get_service_provider(
        self, service_id: ServiceId[ServiceType]
    ) -> ServiceProvider[ServiceType]:
        return self._services.get_service_provider(service_id)

    def get_service_group_providers(
        self, group_id: ServiceId[ServiceType]
    ) -> Iterable[ServiceProvider[ServiceType]]:
        return self._services.get_service_group_providers(group_id)

    def run(self) -> None:
        with self._context_client.open_context(
            OnemlSessionContextIds.SESSION_ID, self._session_id
        ):
            self._running_session_registry.set(self._session_id, self)
            # with self._session_context.execution_context(self):
            self._session_state_client.set_state(PipelineSessionState.RUNNING)
            while self._session_state_client.get_state() == PipelineSessionState.RUNNING:
                self._session_frame.tick()
            self._running_session_registry.unset(self._session_id)

    def run_node(self, node: PipelineNode) -> None:
        self._session_state_client.set_state(PipelineSessionState.RUNNING)
        self.session_executables_client().execute_node(node)

    def stop(self) -> None:
        self._session_state_client.set_state(PipelineSessionState.STOPPED)

    def session_id(self) -> PipelineSessionId:
        return self._session_id

    def pipeline_frame_client(self) -> IPipelineSessionFrame:
        return self._session_frame

    def pipeline_state_client(self) -> IManagePipelineSessionState:
        return self._session_state_client

    def pipeline_loader_getter(self) -> IGetLoaders[Any]:
        return self._pipeline_loader_getter

    def pipeline_publisher_getter(self) -> IGetPublishers[Any]:
        return self._pipeline_publisher_getter

    def session_executables_client(self) -> IManagePipelineNodeExecutables:
        return self._session_executables_client

    def node_state_client(self) -> IManagePipelineNodeState:
        return self._node_state_client

    def node_executables_client(self) -> IManagePipelineNodeExecutables:
        return self._node_executables_client
